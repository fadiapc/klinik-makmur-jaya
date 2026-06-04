"""
security.py — Cryptographic utilities for Klinik Makmur Jaya.

Responsibilities
────────────────
1. Password hashing  — passlib[bcrypt] with CryptContext
2. JWT management    — PyJWT for access tokens, refresh tokens, and
                       short-lived email-verification tokens
3. Rate-limiting     — shared slowapi Limiter instance (imported by routes)

Design notes
────────────
• PyJWT >= 2.0 encode() returns str directly — no need for .decode().
• All timestamps in tokens are UTC-aware (datetime.now(timezone.utc)).
• Three distinct token types ("access", "refresh", "email_verify") prevent
  token misuse across endpoints (a refresh token cannot authenticate a request
  that expects an access token).
• The email-verification OTP is itself a signed JWT valid for 10 minutes —
  no extra database table needed.
• The slowapi Limiter uses the real client IP (X-Forwarded-For aware via
  get_remote_address).  app.state.limiter is set in main.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Password hashing ──────────────────────────────────────────────────────────

# schemes list order matters: first scheme is the active hasher; the rest are
# legacy schemes that verify() can still validate (useful for migrations).
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # OWASP recommended minimum: 10; 12 is a safe balance
)


def hash_password(plain_password: str) -> str:
    """
    Return the bcrypt hash of *plain_password*.

    Uses 12 salt rounds — computationally expensive enough to resist offline
    brute-force while remaining fast enough for a real-time login flow
    (≈ 200–300 ms on commodity hardware).
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify *plain_password* against *hashed_password*.

    Returns True on success, False on mismatch.  Never raises — exceptions
    from the underlying C library are caught and logged.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as exc:  # pragma: no cover
        logger.warning("Password verification error: %s", exc)
        return False


# ── JWT helpers ───────────────────────────────────────────────────────────────

_TOKEN_TYPE_CLAIM = "token_type"


def _encode(payload: dict[str, Any]) -> str:
    """Low-level JWT encoder. Always uses settings.SECRET_KEY + ALGORITHM."""
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode(token: str) -> dict[str, Any]:
    """
    Low-level JWT decoder with strict algorithm pinning.

    Raises:
        jwt.ExpiredSignatureError — token expired (caller maps to 401)
        jwt.InvalidTokenError     — any other JWT integrity failure
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],  # explicit allowlist prevents algorithm confusion
    )


# ── Access token ──────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    user_id: int,
    role: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:     The user's public UUID (safe to embed in the token).
        user_id:     Internal DB id — included so dependencies can load the
                     full User object without a second lookup by UUID.
        role:        Role name string (e.g. "admin", "pasien").
        extra_claims: Optional additional claims merged into the payload.
        expires_delta: Override expiry; defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,           # RFC-7519 subject = public UUID
        "uid": user_id,           # internal id for fast DB lookup
        "role": role,
        _TOKEN_TYPE_CLAIM: "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return _encode(payload)


def create_refresh_token(subject: str, user_id: int) -> str:
    """
    Create a long-lived refresh token.

    Refresh tokens contain minimal claims — just enough to identify the user
    so the endpoint can issue a new access token.  They must NOT be used for
    resource authorization.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": subject,
        "uid": user_id,
        _TOKEN_TYPE_CLAIM: "refresh",
        "iat": now,
        "exp": expire,
    }
    return _encode(payload)


def create_email_verification_token(email: str) -> str:
    """
    Create a short-lived (10 min) signed token for email OTP verification.

    The token is emailed to the user as a URL parameter.  On the verify-email
    endpoint, this token is decoded and the user's is_verified flag is set.

    Using a signed JWT avoids needing a separate verification_tokens table.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=10)
    payload: dict[str, Any] = {
        "sub": email,
        _TOKEN_TYPE_CLAIM: "email_verify",
        "iat": now,
        "exp": expire,
    }
    return _encode(payload)


# ── Token decoding (typed) ────────────────────────────────────────────────────

def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate an access token.

    Raises:
        jwt.ExpiredSignatureError if expired.
        jwt.InvalidTokenError if tampered, wrong algorithm, or wrong type.
    """
    payload = _decode(token)
    if payload.get(_TOKEN_TYPE_CLAIM) != "access":
        raise InvalidTokenError("Token is not an access token.")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a refresh token.

    Raises:
        jwt.ExpiredSignatureError if expired.
        jwt.InvalidTokenError if wrong type or tampered.
    """
    payload = _decode(token)
    if payload.get(_TOKEN_TYPE_CLAIM) != "refresh":
        raise InvalidTokenError("Token is not a refresh token.")
    return payload


def decode_email_verification_token(token: str) -> str:
    """
    Decode an email-verification token.

    Returns the email address embedded as the subject claim.

    Raises:
        jwt.ExpiredSignatureError if the 10-minute window has passed.
        jwt.InvalidTokenError if tampered or wrong type.
    """
    payload = _decode(token)
    if payload.get(_TOKEN_TYPE_CLAIM) != "email_verify":
        raise InvalidTokenError("Token is not an email-verification token.")
    email: str = payload["sub"]
    return email


# ── Rate limiter singleton ────────────────────────────────────────────────────

# Imported by main.py and auth_routes.py.
# main.py binds it to app.state.limiter and registers the exception handler.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],   # global safety net; routes add stricter limits
)
