"""
user_repository.py — Data Access Layer for the users table.

All methods are async and receive an AsyncSession from the get_db() dependency.
This layer is responsible ONLY for SQL — no business logic, no HTTP concerns.

Naming convention:
  get_*     — SELECT queries, return ORM object or None
  create_*  — INSERT, return the new ORM object
  update_*  — UPDATE, return the updated ORM object
  exists_*  — EXISTS check, return bool (cheaper than a full SELECT)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Role, User

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Encapsulates all database queries for the users table.

    Instantiate with an AsyncSession:
        repo = UserRepository(db)
        user = await repo.get_by_email("x@y.com")
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Lookups ───────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Fetch a user by internal BigInteger PK.

        Eagerly loads the related Role to avoid lazy-load errors outside the
        session context (since `role` relationship uses lazy="joined").
        """
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid: str) -> Optional[User]:
        """Fetch a user by public UUID (used in API responses)."""
        result = await self.db.execute(
            select(User)
            .where(User.uuid == uuid)
            .options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by email address.

        Email comparison is case-insensitive (lower()) to prevent duplicate
        accounts created with different casing (e.g. User@email.com vs user@email.com).
        The DB stores emails normalised to lowercase (enforced in create()).
        """
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower().strip())
            .options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """
        Return True if an account with *email* already exists.

        Uses EXISTS semantics via LIMIT 1 — faster than COUNT(*) on large tables.
        """
        result = await self.db.execute(
            select(User.id)
            .where(User.email == email.lower().strip())
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    # ── Role helpers ──────────────────────────────────────────────────────────

    async def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """Fetch a Role row by its name string (e.g. 'pasien', 'admin')."""
        result = await self.db.execute(
            select(Role).where(Role.name == role_name.lower().strip())
        )
        return result.scalar_one_or_none()

    # ── Writes ────────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role_id: int,
        phone: Optional[str] = None,
        is_verified: bool = False,
    ) -> User:
        """
        Insert a new user row and flush to get the auto-assigned id and uuid.

        Does NOT commit — the caller's session (get_db) commits on success.
        Normalises email to lowercase before saving.
        """
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=password_hash,
            role_id=role_id,
            phone=phone,
            is_verified=is_verified,
        )
        self.db.add(user)
        await self.db.flush()          # populates user.id, user.uuid from DB defaults
        await self.db.refresh(user)    # reload all server-default columns
        # Eagerly load the role relationship so callers get a fully-formed object
        await self.db.refresh(user, attribute_names=["role"])
        logger.info(
            "New user created | id=%d email=%s role_id=%d",
            user.id,
            user.email,
            user.role_id,
        )
        return user

    async def update_last_login(self, user: User) -> User:
        """Stamp the last_login_at column with the current UTC time."""
        user.last_login_at = datetime.now(timezone.utc)
        self.db.add(user)
        await self.db.flush()
        return user

    async def set_email_verified(self, user: User) -> User:
        """Mark the user's email as verified."""
        user.is_verified = True
        self.db.add(user)
        await self.db.flush()
        return user

    async def set_active(self, user: User, *, active: bool) -> User:
        """Enable or soft-disable an account without physical deletion."""
        user.is_active = active
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_password_hash(self, user: User, new_hash: str) -> User:
        """Replace the password hash (used by change-password flow)."""
        user.password_hash = new_hash
        self.db.add(user)
        await self.db.flush()
        return user
