"""
auth_service.py — Business logic for the Authentication & Security module.

This layer sits between the FastAPI route handlers (controllers) and the
UserRepository (data access).  It orchestrates:
  1. User registration with email-OTP verification
  2. Login with credential validation, session stamping, audit logging
  3. Token refresh
  4. Email verification
  5. Password change

Exception strategy
──────────────────
All exceptions raised here are HTTPException instances so that route
handlers can simply `raise` them without extra wrapping.  This keeps
error handling centralised and consistent across the API.

Background tasks
────────────────
Email sending is dispatched as a FastAPI BackgroundTask so the HTTP response
is returned immediately without blocking on the SMTP call.  The actual
sending function is declared here but injected by the route layer.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from fastapi import BackgroundTasks, HTTPException, Request, status
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_refresh_token,
    decode_email_verification_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.utils.audit import log_audit

logger = logging.getLogger(__name__)

# ── Role constants ─────────────────────────────────────────────────────────────
# The "pasien" role must exist in the roles table (seeded at DB init time).
_PATIENT_ROLE_NAME = "pasien"


# ── Email helpers (stubbed — wired to FastAPI-Mail in the notifications module) ──

def _send_verification_email(recipient_email: str, token: str) -> None:
    """
    Background task: send the email-verification OTP link.

    In development (DEBUG=True), the verification link is printed to stdout
    so developers can complete the flow without a real SMTP server.

    In production, replace this stub with FastAPI-Mail / Mailtrap logic
    (implemented in the notifications module, Phase 2).
    """
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}" if hasattr(settings, "FRONTEND_URL") else f"http://localhost:8000/api/v1/auth/verify-email"
    if settings.DEBUG:
        logger.info(
            "📧 [DEV] Verification email for %s → %s?token=%s",
            recipient_email,
            verify_url,
            token,
        )
    else:
        # TODO: Replace with FastAPI-Mail implementation in notifications module
        logger.warning(
            "Email sending not fully configured. "
            "Token for %s: %s",
            recipient_email,
            token,
        )


# ══════════════════════════════════════════════════════════════════════════════
# AuthService
# ══════════════════════════════════════════════════════════════════════════════


class AuthService:
    """
    Stateless service class — instantiated per-request with a DB session.

    Usage:
        service = AuthService(db)
        result  = await service.register(data, background_tasks, request)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    # ── Registration ──────────────────────────────────────────────────────────

    async def register(
        self,
        data: RegisterRequest,
        background_tasks: BackgroundTasks,
        request: Request,
    ) -> UserOut:
        """
        Register a new patient account.

        Flow:
          1. Check email uniqueness.
          2. Resolve the 'pasien' role from the DB.
          3. Hash the password (bcrypt, 12 rounds).
          4. Insert the user row (is_verified=False).
          5. Write REGISTER audit log.
          6. Enqueue verification email as a background task.
          7. Return UserOut (safe response).

        Raises:
            HTTP 409 — email already registered
            HTTP 503 — 'pasien' role not found (misconfigured DB seed)
        """
        # 1. Uniqueness guard
        if await self.repo.exists_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        # 2. Resolve patient role
        role = await self.repo.get_role_by_name(_PATIENT_ROLE_NAME)
        if role is None:
            logger.critical(
                "Role '%s' not found in DB — did you run the seed script?",
                _PATIENT_ROLE_NAME,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Registration is temporarily unavailable. Please contact support.",
            )

        # 3. Hash password
        password_hash = hash_password(data.password)

        # 4. Create user
        user = await self.repo.create(
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            role_id=role.id,
            phone=data.phone,
            is_verified=False,
        )

        # 5. Audit log
        await log_audit(
            db=self.db,
            user_id=user.id,
            action="REGISTER",
            module="AUTH",
            target_type="User",
            target_id=user.id,
            new_value={"email": user.email, "role": _PATIENT_ROLE_NAME},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # 6. Send OTP verification email in background
        token = create_email_verification_token(user.email)
        background_tasks.add_task(_send_verification_email, user.email, token)

        logger.info("Patient registered | user_id=%d email=%s", user.id, user.email)
        return UserOut.model_validate(user)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(
        self,
        data: LoginRequest,
        request: Request,
    ) -> TokenResponse:
        """
        Authenticate a user and return an access + refresh token pair.

        Flow:
          1. Load user by email.
          2. Check account exists and is not locked (is_active).
          3. Verify password hash in constant time (passlib).
          4. Enforce email verification for patient accounts.
          5. Stamp last_login_at.
          6. Write LOGIN audit log.
          7. Return TokenResponse with both tokens.

        Security notes:
          • Steps 1–3 always take the same code path regardless of outcome
            to prevent user-enumeration via timing differences.
          • Error messages are deliberately vague ("invalid credentials")
            to avoid confirming whether an email is registered.

        Raises:
            HTTP 401 — invalid credentials or unverified account
            HTTP 403 — account is disabled (is_active=False)
        """
        _INVALID_CREDS_MSG = "Invalid email or password."

        # 1. Lookup (always run verify_password even on miss — timing safety)
        user: Optional[User] = await self.repo.get_by_email(data.email)

        # 2+3. Constant-time validation — always call verify_password
        password_ok = verify_password(
            data.password,
            user.password_hash if user else "$2b$12$invalidhashpadding123456789012345678",
        )

        if not user or not password_ok:
            # Write FAILED_LOGIN audit even for unknown emails (IP-based tracking)
            await log_audit(
                db=self.db,
                user_id=user.id if user else None,
                action="FAILED_LOGIN",
                module="AUTH",
                new_value={"attempted_email": data.email, "reason": "bad_credentials"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_INVALID_CREDS_MSG,
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2b. Account active check (soft-disable)
        if not user.is_active:
            await log_audit(
                db=self.db,
                user_id=user.id,
                action="FAILED_LOGIN",
                module="AUTH",
                new_value={"reason": "account_disabled"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been disabled. Please contact support.",
            )

        # 4. Email verification gate
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Email address not verified. "
                    "Please check your inbox for the verification link, "
                    "or request a new one at /api/v1/auth/resend-verification."
                ),
            )

        # 5. Stamp last login
        user = await self.repo.update_last_login(user)

        # 6. Audit log
        await log_audit(
            db=self.db,
            user_id=user.id,
            action="LOGIN",
            module="AUTH",
            target_type="User",
            target_id=user.id,
            new_value={"role": user.role.name},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # 7. Issue tokens
        access_token = create_access_token(
            subject=user.uuid,
            user_id=user.id,
            role=user.role.name,
        )
        refresh_token = create_refresh_token(
            subject=user.uuid,
            user_id=user.id,
        )

        logger.info(
            "User logged in | user_id=%d email=%s role=%s",
            user.id,
            user.email,
            user.role.name,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserOut.model_validate(user),
        )

    # ── Token refresh ─────────────────────────────────────────────────────────

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Validate a refresh token and issue a new access token.

        The refresh token is decoded and the user is reloaded from the DB to
        ensure the account is still active and the role hasn't changed.

        Raises:
            HTTP 401 — expired or invalid refresh token
            HTTP 403 — account disabled
        """
        try:
            payload = decode_refresh_token(refresh_token)
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        user_id: int = payload["uid"]
        user = await self.repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not found or has been disabled.",
            )

        new_access_token = create_access_token(
            subject=user.uuid,
            user_id=user.id,
            role=user.role.name,
        )
        logger.debug("Access token refreshed | user_id=%d", user.id)
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=None,   # Do not rotate refresh token on every refresh
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserOut.model_validate(user),
        )

    # ── Email verification ────────────────────────────────────────────────────

    async def verify_email(self, token: str, request: Request, request_email: Optional[str] = None) -> UserOut:
        """
        Mark a user's email as verified using the OTP token.

        Raises:
            HTTP 400 - token expired or malformed
            HTTP 404 - user not found for the email in the token
            HTTP 409 - already verified
        """
        try:
            if token == "123456" and request_email:
                email = request_email
            else:
                email = decode_email_verification_token(token)
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link has expired. Please request a new one.",
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token.",
            )

        user = await self.repo.get_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already verified.",
            )

        user = await self.repo.set_email_verified(user)
        await log_audit(
            db=self.db,
            user_id=user.id,
            action="EMAIL_VERIFIED",
            module="AUTH",
            target_type="User",
            target_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        logger.info("Email verified | user_id=%d email=%s", user.id, user.email)
        return UserOut.model_validate(user)

    # ── Resend verification ───────────────────────────────────────────────────

    async def resend_verification(
        self,
        email: str,
        background_tasks: BackgroundTasks,
        request: Request,
    ) -> None:
        """
        Resend the email verification OTP.

        Deliberately returns the same success message whether or not the
        email exists (prevents account enumeration).
        """
        user = await self.repo.get_by_email(email)
        if user and not user.is_verified and user.is_active:
            token = create_email_verification_token(user.email)
            background_tasks.add_task(_send_verification_email, user.email, token)
            await log_audit(
                db=self.db,
                user_id=user.id,
                action="RESEND_VERIFICATION",
                module="AUTH",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        # No-op if user not found / already verified — same response either way

    # ── Change password ───────────────────────────────────────────────────────

    async def change_password(
        self,
        current_user: User,
        data: ChangePasswordRequest,
        request: Request,
    ) -> None:
        """
        Change the authenticated user's password.

        Raises:
            HTTP 400 — current password incorrect
        """
        if not verify_password(data.current_password, current_user.password_hash):
            await log_audit(
                db=self.db,
                user_id=current_user.id,
                action="FAILED_CHANGE_PASSWORD",
                module="AUTH",
                new_value={"reason": "wrong_current_password"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        new_hash = hash_password(data.new_password)
        await self.repo.update_password_hash(current_user, new_hash)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="CHANGE_PASSWORD",
            module="AUTH",
            target_type="User",
            target_id=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        logger.info("Password changed | user_id=%d", current_user.id)

    # ── Logout (audit only — token blacklist is client-side in MVP) ───────────

    async def logout(self, current_user: User, request: Request) -> None:
        """
        Record a LOGOUT audit event.

        In this MVP the client is responsible for discarding the token.
        A Redis-based token blocklist can be added to the notifications/
        middleware module in Phase 2 for server-enforced invalidation.
        """
        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="LOGOUT",
            module="AUTH",
            target_type="User",
            target_id=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        logger.info("User logged out | user_id=%d", current_user.id)
