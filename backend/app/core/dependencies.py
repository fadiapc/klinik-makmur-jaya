"""
dependencies.py — FastAPI dependency functions for authentication & RBAC.

This module provides three public symbols:

  1. get_current_user(token) → User
       Decodes and validates the Bearer token from Authorization header.
       Raises HTTP 401 if the token is missing, expired, or tampered.

  2. get_current_active_user(user) → User
       Builds on get_current_user; additionally asserts is_active=True.
       Raises HTTP 403 if the account is disabled.

  3. require_role(*roles: RoleName) → Callable → User
       Factory that returns a FastAPI dependency enforcing at least one of
       the specified roles.  Usage:

           @router.get("/admin-only")
           async def admin_route(
               user: User = Depends(require_role(RoleName.ADMIN))
           ):
               ...

  4. RoleName
       String enum of all valid role names, matching the roles table seed data.

Design decisions
────────────────
• OAuth2PasswordBearer is used as the token extractor because it:
    - Integrates with Swagger UI's "Authorize" button automatically.
    - Raises a 401 with the correct WWW-Authenticate header on missing tokens.
• The token payload includes `uid` (internal PK) so get_current_user can
  load the full User object in a single indexed query.
• `selectinload(User.role)` is used explicitly to avoid N+1 queries when
  the role name is accessed inside require_role.
"""

from __future__ import annotations

import enum
import logging
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# ── OAuth2 scheme — auto-populates Swagger UI "Authorize" ────────────────────

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT Bearer Token",
    description="Paste the `access_token` value returned by /login.",
)


# ── Role constants ────────────────────────────────────────────────────────────


class RoleName(str, enum.Enum):
    """
    Canonical role name constants — must match the `name` column in the
    `roles` table (seeded at DB init time).

    Usage in route decorators:
        Depends(require_role(RoleName.ADMIN, RoleName.APOTEKER))
    """

    ADMIN = "admin"
    APOTEKER = "apoteker"
    KASIR = "kasir"
    PASIEN = "pasien"


# ── Core dependency: get_current_user ─────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency — decode the Bearer token and return the User object.

    Raises:
        HTTP 401 (UNAUTHORIZED) — token is missing, expired, invalid, or the
                                   user_id embedded in the token no longer exists
                                   in the database.

    This dependency is injected into every protected endpoint, either directly
    or via the `require_role` factory.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please refresh or log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception

    # Extract internal user ID from the token payload
    user_id: int | None = payload.get("uid")
    if user_id is None:
        raise credentials_exception

    # Load the full User object — single indexed PK query
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        logger.warning(
            "Token references non-existent user_id=%s — token may be stale.",
            user_id,
        )
        raise credentials_exception

    return user


# ── Derived dependency: get_current_active_user ───────────────────────────────


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency — assert the authenticated user account is active.

    Raises:
        HTTP 403 (FORBIDDEN) — account has been soft-disabled by an Admin.

    Use this (instead of get_current_user) as the base for any endpoint that
    should be inaccessible to suspended accounts.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your account has been suspended. "
                "Please contact the clinic administration."
            ),
        )
    return current_user


# ── RBAC factory: require_role ────────────────────────────────────────────────


def require_role(*allowed_roles: RoleName) -> Callable:
    """
    Dependency factory for Role-Based Access Control.

    Returns a FastAPI-compatible async dependency that:
      1. Calls get_current_active_user (which calls get_current_user).
      2. Compares the user's role against the allowed_roles list.
      3. Returns the User on success.
      4. Raises HTTP 403 if the role is insufficient.

    Args:
        *allowed_roles: One or more RoleName enum members that are permitted
                        to access the decorated endpoint.

    Usage:
        # Single role
        @router.get("/pharmacist-only")
        async def rx_queue(user: User = Depends(require_role(RoleName.APOTEKER))):
            ...

        # Multiple roles
        @router.get("/staff-only")
        async def staff_view(
            user: User = Depends(require_role(RoleName.ADMIN, RoleName.KASIR))
        ):
            ...

    Returns:
        A coroutine function (async def) suitable as a FastAPI Depends() argument.
    """
    # Materialise the allowed set once at decoration time for O(1) lookup
    _allowed: set[str] = {r.value for r in allowed_roles}

    async def _role_dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role: str = current_user.role.name
        if user_role not in _allowed:
            logger.warning(
                "Access denied | user_id=%d role=%s required_roles=%s path=<omitted>",
                current_user.id,
                user_role,
                sorted(_allowed),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. This endpoint requires one of the following "
                    f"roles: {sorted(_allowed)}. Your role is '{user_role}'."
                ),
            )
        return current_user

    # Preserve a readable name for FastAPI's dependency graph / OpenAPI docs
    _role_dependency.__name__ = (
        f"require_role({'|'.join(sorted(_allowed))})"
    )

    return _role_dependency


# ── Convenience pre-built dependencies ────────────────────────────────────────
# These cover the most common RBAC patterns and can be used directly in Depends()
# without calling require_role() each time.

RequireAdmin = require_role(RoleName.ADMIN)
RequireApoteker = require_role(RoleName.APOTEKER)
RequireKasir = require_role(RoleName.KASIR)
RequirePasien = require_role(RoleName.PASIEN)

RequireAdminOrApoteker = require_role(RoleName.ADMIN, RoleName.APOTEKER)
RequireAdminOrKasir = require_role(RoleName.ADMIN, RoleName.KASIR)
RequireStaff = require_role(RoleName.ADMIN, RoleName.APOTEKER, RoleName.KASIR)
