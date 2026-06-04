from typing import Sequence

from fastapi import HTTPException, status

from app.models.models import AuditLog, User
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.audit import AuditLogOut, DashboardStatsOut


class AuditLogService:
    def __init__(self, repo: AuditLogRepository):
        self.repo = repo

    def _ensure_admin(self, user: User) -> None:
        """Check if user has admin role."""
        if not user.role or user.role.name.lower() != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

    async def get_dashboard_stats(self, current_user: User) -> DashboardStatsOut:
        self._ensure_admin(current_user)

        auth_stats = await self.repo.get_login_stats_today()
        hourly_activity = await self.repo.get_hourly_activity_today()
        authorization_stats = await self.repo.get_authorization_stats()

        return DashboardStatsOut(
            auth_stats=auth_stats,
            hourly_activity=hourly_activity,
            authorization_stats=authorization_stats,
        )

    async def list_audit_logs(
        self, q: str | None, current_user: User, limit: int = 50
    ) -> list[AuditLogOut]:
        self._ensure_admin(current_user)
        
        logs = await self.repo.list_audit_logs(q=q, limit=limit)
        
        results = []
        for log in logs:
            email = log.user.email if log.user else "System / Unknown"
            role_name = log.user.role.name if log.user and log.user.role else "N/A"
            
            # Determine status based on action string
            status_label = "Failed" if "FAILED" in log.action else "Success"
            
            results.append(
                AuditLogOut(
                    id=log.id,
                    created_at=log.created_at,
                    email=email,
                    role_name=role_name,
                    action=log.action,
                    module=log.module,
                    ip_address=log.ip_address or "Unknown",
                    status=status_label
                )
            )
            
        return results
