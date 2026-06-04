import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.models.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate, UserFilterParams
from app.schemas.auth import UserOut, RoleOut
from app.utils.audit import log_audit

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def _ensure_admin(self, current_user: User) -> None:
        if current_user.role.name.lower() != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Only Administrators can perform this action."
            )

    async def list_users(
        self,
        filters: UserFilterParams,
        page: int,
        page_size: int,
        current_user: User,
    ) -> PaginatedResponse[UserOut]:
        self._ensure_admin(current_user)
        users, total = await self.repo.list_users(filters, page, page_size)
        items = [UserOut.model_validate(u) for u in users]
        return PaginatedResponse.build(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_user(
        self,
        data: UserCreate,
        current_user: User,
        request: Request,
    ) -> UserOut:
        self._ensure_admin(current_user)

        if await self.repo.exists_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {data.email} already exists."
            )

        hashed_password = hash_password(data.password)
        
        user = await self.repo.create(
            name=data.name,
            email=data.email,
            password_hash=hashed_password,
            role_id=data.role_id,
            phone=data.phone,
            is_verified=True,  # Users created by admin are auto-verified
        )

        await self.repo.set_active(user, active=data.is_active)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="CREATE_USER",
            module="AUTH",
            target_type="User",
            target_id=user.id,
            new_value={"email": user.email, "role_id": user.role_id, "name": user.name},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        logger.info(f"User created: {user.email} by Admin {current_user.email}")
        return UserOut.model_validate(user)

    async def update_user(
        self,
        user_uuid: str,
        data: UserUpdate,
        current_user: User,
        request: Request,
    ) -> UserOut:
        self._ensure_admin(current_user)

        user = await self.repo.get_by_uuid(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_uuid} not found."
            )

        # Build update dict
        update_dict: dict = {
            k: v for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None
        }

        if "email" in update_dict and update_dict["email"] != user.email:
            if await self.repo.exists_by_email(update_dict["email"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email {update_dict['email']} is already taken."
                )

        old_snapshot = {
            "name": user.name,
            "email": user.email,
            "role_id": user.role_id,
            "phone": user.phone,
            "is_active": user.is_active,
        }

        updated_user = await self.repo.update(user, update_dict)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="UPDATE_USER",
            module="AUTH",
            target_type="User",
            target_id=user.id,
            old_value=old_snapshot,
            new_value=update_dict,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return UserOut.model_validate(updated_user)

    async def toggle_user_status(
        self,
        user_uuid: str,
        current_user: User,
        request: Request,
    ) -> UserOut:
        self._ensure_admin(current_user)

        user = await self.repo.get_by_uuid(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_uuid} not found."
            )

        # Prevent admin from deactivating themselves
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account."
            )

        new_status = not user.is_active
        updated_user = await self.repo.set_active(user, active=new_status)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="TOGGLE_USER_STATUS",
            module="AUTH",
            target_type="User",
            target_id=user.id,
            old_value={"is_active": not new_status},
            new_value={"is_active": new_status},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return UserOut.model_validate(updated_user)

    async def list_roles(self, current_user: User) -> list[RoleOut]:
        self._ensure_admin(current_user)
        roles = await self.repo.list_roles()
        return [RoleOut.model_validate(r) for r in roles]
