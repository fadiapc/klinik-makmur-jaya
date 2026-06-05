"""
auth_routes.py — FastAPI router for the Authentication & Security module.

Implements PRD Section 4.1 (AUTH-01 through AUTH-06):

  POST /api/v1/auth/register          Register a new patient account
  POST /api/v1/auth/login             Login (all roles) → access + refresh tokens
  POST /api/v1/auth/logout            Record logout event (client drops token)
  POST /api/v1/auth/refresh           Exchange refresh token → new access token
  POST /api/v1/auth/verify-email      Verify email using OTP token
  POST /api/v1/auth/resend-verification  Resend OTP verification email
  POST /api/v1/auth/change-password   Change authenticated user's password
  GET  /api/v1/auth/me                Return current user's profile

Security measures applied here:
  • AUTH-04 Rate limiting (slowapi):
      /register  → 5 per minute per IP
      /login     → 10 per minute per IP  (blocks brute-force)
  • AUTH-05 Token expiry: handled in security.py (30 min access, 7 day refresh)
  • AUTH-06 Audit logging: every action writes to audit_logs via AuthService

Note on /login content type:
  The endpoint accepts application/json (LoginRequest) NOT form data, to keep
  the API consistent.  The OAuth2PasswordBearer scheme is used only for token
  extraction in protected endpoints (the tokenUrl is informational for Swagger).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import limiter
from app.models.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    EmailVerifyRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/auth",
    tags=["🔐 Authentication"],
)


# ── Helper: build AuthService from DB session ──────────────────────────────────

def _get_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency factory — provides an AuthService bound to the request session."""
    return AuthService(db)


# ══════════════════════════════════════════════════════════════════════════════
# Public endpoints (no Bearer token required)
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient account (AUTH-02)",
    description=(
        "Creates a new Pasien (patient) account. "
        "After registration, a verification link is sent to the provided email. "
        "The account cannot be used to log in until the email is verified. "
        "**Rate limited: 5 requests per minute per IP.**"
    ),
    responses={
        201: {"description": "Account created — verification email dispatched"},
        409: {"description": "Email address already registered"},
        422: {"description": "Validation error (password policy, email format, etc.)"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Service temporarily unavailable (DB seed issue)"},
    },
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(_get_service),
) -> RegisterResponse:
    """
    Register a new patient.

    - Validates password strength (PRD AUTH-03).
    - Checks email uniqueness.
    - Hashes password with bcrypt (12 rounds).
    - Sends OTP verification email (background task).
    - Writes REGISTER audit log.
    """
    user_out = await service.register(data, background_tasks, request)
    return RegisterResponse(user=user_out)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login — all roles (AUTH-01)",
    description=(
        "Authenticates a user and returns a JWT access token and refresh token. "
        "The `role` field in the response determines the dashboard to display. "
        "**Rate limited: 10 requests per minute per IP (brute-force protection).**"
    ),
    responses={
        200: {"description": "Login successful — token pair returned"},
        401: {"description": "Invalid credentials or unverified email"},
        403: {"description": "Account disabled"},
        429: {"description": "Too many login attempts — try again later"},
    },
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    """
    Authenticate any role (Admin, Apoteker, Kasir, Pasien).

    - Performs constant-time credential check (prevents user enumeration).
    - Enforces email verification gate for patient accounts.
    - Stamps `last_login_at`.
    - Writes LOGIN / FAILED_LOGIN audit log.
    - Returns `access_token` (30 min) + `refresh_token` (7 days).
    """
    return await service.login(data, request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description=(
        "Exchange a valid refresh token for a new access token. "
        "The refresh token is NOT rotated (same token can be reused until expiry). "
        "Implement token rotation in Phase 2 with a Redis blocklist."
    ),
    responses={
        200: {"description": "New access token issued"},
        401: {"description": "Refresh token expired or invalid"},
        403: {"description": "Account disabled"},
    },
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    """Validate a refresh token and issue a new access token."""
    return await service.refresh_access_token(data.refresh_token)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address using OTP token (AUTH-02)",
    description=(
        "Submit the token received via email to activate your account. "
        "Tokens expire after **10 minutes**. "
        "Request a new token at `/resend-verification` if yours has expired."
    ),
    responses={
        200: {"description": "Email verified — account is now active"},
        400: {"description": "Token expired or invalid"},
        404: {"description": "User not found for this token"},
        409: {"description": "Email already verified"},
    },
)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    data: EmailVerifyRequest,
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    """Decode OTP token and set is_verified=True on the user's account."""
    await service.verify_email(data.token, request, getattr(data, "email", None))
    return MessageResponse(
        message="Email verified successfully. You may now log in."
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend email verification OTP",
    description=(
        "Request a new verification email. "
        "Always returns success to prevent account enumeration. "
        "**Rate limited: 3 requests per minute per IP.**"
    ),
)
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    """Resend the OTP verification email (silently no-ops on unknown emails)."""
    await service.resend_verification(data.email, background_tasks, request)
    return MessageResponse(
        message=(
            "If an unverified account with that email exists, "
            "a new verification link has been sent."
        )
    )


# ══════════════════════════════════════════════════════════════════════════════
# Protected endpoints (Bearer token required)
# ══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user's profile",
    description=(
        "Returns the profile of the currently authenticated user. "
        "Requires a valid Bearer token in the Authorization header."
    ),
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Token missing, expired, or invalid"},
        403: {"description": "Account disabled"},
    },
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    """Return the current user's safe profile representation."""
    return UserOut.model_validate(current_user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout — record audit event (AUTH-05/06)",
    description=(
        "Records a LOGOUT audit log entry. "
        "The client is responsible for discarding the access and refresh tokens. "
        "Server-side token invalidation via Redis blocklist can be added in Phase 2."
    ),
    responses={
        200: {"description": "Logout recorded"},
        401: {"description": "Token missing or invalid"},
    },
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    """Write LOGOUT audit log. Client must discard both tokens."""
    await service.logout(current_user, request)
    return MessageResponse(
        message="Logged out successfully. Please discard your tokens."
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change authenticated user's password (AUTH-03)",
    description=(
        "Change your password. Requires the current password to be provided. "
        "New password must satisfy the same strength policy as registration. "
        "**Rate limited: 5 requests per minute per IP.**"
    ),
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Current password incorrect or new passwords don't match"},
        401: {"description": "Token missing or invalid"},
        422: {"description": "Password strength validation failed"},
    },
)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    """Verify current password then replace hash. Writes audit log."""
    await service.change_password(current_user, data, request)
    return MessageResponse(
        message="Password changed successfully. Please log in again with your new password."
    )
