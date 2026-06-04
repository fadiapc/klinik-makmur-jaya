from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.audit import AuditLogOut, DashboardStatsOut
from app.services.audit_service import AuditLogService

router = APIRouter(prefix="/audit", tags=["Audit Log Management"])


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditLogService:
    repo = AuditLogRepository(db)
    return AuditLogService(repo)


@router.get("/stats", response_model=DashboardStatsOut)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    audit_service: AuditLogService = Depends(get_audit_service),
) -> Any:
    """Get statistics for the Audit Dashboard (Admin only)."""
    return await audit_service.get_dashboard_stats(current_user)


@router.get("/logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    q: str | None = Query(None, description="Fuzzy search across action, module, email, and IP"),
    limit: int = Query(50, ge=1, le=500, description="Number of recent logs to fetch"),
    current_user: User = Depends(get_current_user),
    audit_service: AuditLogService = Depends(get_audit_service),
) -> Any:
    """Fetch recent audit logs with fuzzy search (Admin only)."""
    return await audit_service.list_audit_logs(q, current_user, limit)
