"""
auth.py (schemas) — Pydantic request/response models for the auth module.

All input schemas perform validation at the boundary so that controllers
and services receive clean, typed data without defensive checks.

Password policy (PRD AUTH-03):
  • Minimum 8 characters
  • At least 1 uppercase letter
  • At least 1 lowercase letter
  • At least 1 digit
  • At least 1 special character from the allowed set
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ── Constants ─────────────────────────────────────────────────────────────────

_SPECIAL_CHARS: str = r"""!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~"""
_PASSWORD_REGEX = re.compile(
    r"^"
    r"(?=.*[a-z])"          # at least one lowercase
    r"(?=.*[A-Z])"          # at least one uppercase
    r"(?=.*\d)"             # at least one digit
    rf"(?=.*[{_SPECIAL_CHARS}])"  # at least one special character
    r".{8,}"                # minimum 8 characters total
    r"$"
)


# ── Input schemas ─────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """
    POST /api/v1/auth/register

    Only patients self-register via this endpoint.
    Admin/Apoteker/Kasir accounts are provisioned by Admin (future CRUD module).
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Budi Santoso"],
        description="Full name of the patient",
    )
    email: EmailStr = Field(
        ...,
        examples=["budi@email.com"],
        description="Email address used for login and notifications",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        examples=["MyStr0ng!Pass"],
        description="Password — min 8 chars, must include upper, lower, digit, special char",
    )
    confirm_password: str = Field(
        ...,
        examples=["MyStr0ng!Pass"],
        description="Must match password exactly",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        examples=["08123456789"],
        description="Contact phone number (optional)",
        pattern=r"^[0-9+\-() ]{7,20}$",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce PRD AUTH-03 password complexity rules."""
        if not _PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must be at least 8 characters and contain at least: "
                "one uppercase letter, one lowercase letter, one digit, "
                "and one special character (!@#$%^&* etc.)"
            )
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        """Confirm password and password must be identical."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    """
    POST /api/v1/auth/login

    Accepts credentials for all four roles.
    The response role determines which dashboard the frontend redirects to.
    """

    email: EmailStr = Field(
        ...,
        examples=["admin@klinikmakmurjaya.id"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        examples=["AdminStr0ng!"],
    )


class RefreshTokenRequest(BaseModel):
    """POST /api/v1/auth/refresh — exchange a refresh token for a new access token."""

    refresh_token: str = Field(..., description="Valid refresh token issued at login")


class EmailVerifyRequest(BaseModel):
    """POST /api/v1/auth/verify-email — submit the token received by email."""

    token: str = Field(
        ...,
        description="Email verification token (signed JWT, valid 10 minutes)",
    )


class ResendVerificationRequest(BaseModel):
    """POST /api/v1/auth/resend-verification — request a new OTP email."""

    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """POST /api/v1/auth/change-password (authenticated endpoint)."""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if not _PASSWORD_REGEX.match(v):
            raise ValueError(
                "New password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character."
            )
        return v

    @model_validator(mode="after")
    def new_passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")
        return self


# ── Nested response schemas ───────────────────────────────────────────────────


class RoleOut(BaseModel):
    """Embedded role information returned inside UserOut."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    """
    Safe user representation for API responses.

    Deliberately omits: id (internal), password_hash, role_id.
    The public `uuid` is used instead of `id`.
    """

    uuid: str = Field(description="Public UUID — safe to include in URLs / responses")
    name: str
    email: EmailStr
    phone: Optional[str]
    role: RoleOut
    is_verified: bool
    is_active: bool
    last_login_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 UTC timestamp of most recent login",
    )

    model_config = {"from_attributes": True}


# ── Token response schemas ────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    """
    Standard token response returned after successful login or token refresh.

    Both tokens are included on login.  Only access_token is returned on refresh.
    """

    access_token: str = Field(description="Short-lived JWT for API authorization")
    refresh_token: Optional[str] = Field(
        default=None,
        description="Long-lived JWT; present on login, absent on refresh",
    )
    token_type: str = Field(default="bearer")
    expires_in: int = Field(
        description="Access token lifetime in seconds"
    )
    user: UserOut


class RegisterResponse(BaseModel):
    """Response returned after successful registration."""

    message: str = Field(
        default=(
            "Registration successful. Please check your email and click "
            "the verification link to activate your account."
        )
    )
    user: UserOut


class MessageResponse(BaseModel):
    """Generic success/info message response."""

    message: str
