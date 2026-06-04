from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.auth import UserOut, RoleOut
from app.schemas.user import UserCreate, UserUpdate, UserFilterParams
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User Management"])

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

@router.get("", response_model=PaginatedResponse[UserOut])
async def list_users(
    q: str | None = Query(None, description="Search by name, email, or phone"),
    role_id: int | None = Query(None, description="Filter by role ID"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """List users with pagination and filtering (Admin only)."""
    filters = UserFilterParams(q=q, role_id=role_id, is_active=is_active)
    return await user_service.list_users(filters, page, page_size, current_user)

@router.post("", response_model=UserOut)
async def create_user(
    data: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Create a new user account (Admin only)."""
    return await user_service.create_user(data, current_user, request)

@router.put("/{user_uuid}", response_model=UserOut)
async def update_user(
    user_uuid: str,
    data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Update user details (Admin only)."""
    return await user_service.update_user(user_uuid, data, current_user, request)

@router.put("/{user_uuid}/status", response_model=UserOut)
async def toggle_user_status(
    user_uuid: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Toggle user active status (Admin only)."""
    return await user_service.toggle_user_status(user_uuid, current_user, request)

@router.get("/roles/all", response_model=list[RoleOut])
async def list_roles(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """List all available roles (Admin only)."""
    return await user_service.list_roles(current_user)
