from datetime import datetime, time, timezone
from typing import Sequence

from sqlalchemy import and_, cast, extract, func, or_, select, String, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.models import AuditLog, Role, User


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_login_stats_today(self) -> dict[str, int]:
        """Get login statistics for the current UTC day."""
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)
        
        stmt = select(
            func.sum(cast(AuditLog.action == "LOGIN", Integer)),
            func.sum(cast(AuditLog.action == "FAILED_LOGIN", Integer)),
        ).where(
            AuditLog.created_at >= start_of_day,
            AuditLog.action.in_(["LOGIN", "FAILED_LOGIN"]),
        )
        
        result = await self.db.execute(stmt)
        row = result.first()
        
        success = row[0] or 0
        failed = row[1] or 0
        
        return {
            "total_logins_today": success + failed,
            "successful_logins": success,
            "failed_logins": failed,
        }

    async def get_hourly_activity_today(self) -> list[dict[str, any]]:
        """Get successful vs failed logins grouped by hour for today."""
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)

        # In PostgreSQL, extract('hour' from created_at) returns the hour (0-23)
        stmt = select(
            cast(extract('hour', AuditLog.created_at), Integer).label('hour_num'),
            func.sum(cast(AuditLog.action == "LOGIN", Integer)).label('success'),
            func.sum(cast(AuditLog.action == "FAILED_LOGIN", Integer)).label('failed'),
        ).where(
            AuditLog.created_at >= start_of_day,
            AuditLog.action.in_(["LOGIN", "FAILED_LOGIN"]),
        ).group_by(
            'hour_num'
        ).order_by(
            'hour_num'
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # Initialize 24 hours with 0
        hourly_data = {h: {"success": 0, "failed": 0} for h in range(24)}
        for row in rows:
            hourly_data[row.hour_num]["success"] = row.success
            hourly_data[row.hour_num]["failed"] = row.failed
            
        return [
            {
                "hour": f"{h:02d}:00",
                "success": data["success"],
                "failed": data["failed"]
            }
            for h, data in hourly_data.items()
        ]

    async def get_authorization_stats(self) -> dict[str, int]:
        """
        Get authorization stats. All non-login actions are considered RBAC authorized
        for the sake of the dashboard.
        """
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)
        
        stmt = select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= start_of_day,
            AuditLog.action.not_in(["LOGIN", "FAILED_LOGIN", "LOGOUT", "FAILED_CHANGE_PASSWORD"])
        )
        
        result = await self.db.execute(stmt)
        rbac_count = result.scalar() or 0
        
        return {
            "authorized_all": rbac_count,
            "rbac": rbac_count,
            "obac": 0  # Not implemented yet, as per PRD
        }

    async def list_audit_logs(
        self, q: str | None = None, limit: int = 50
    ) -> Sequence[AuditLog]:
        """Fetch latest audit logs with fuzzy search."""
        stmt = (
            select(AuditLog)
            .options(joinedload(AuditLog.user).joinedload(User.role))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        if q:
            # PostgreSQL ILIKE for fuzzy matching (assumes pg_trgm extension if indexed)
            search_pattern = f"%{q}%"
            # We must outerjoin User to search by email since user_id can be NULL for FAILED_LOGIN
            stmt = stmt.outerjoin(User, AuditLog.user_id == User.id)
            stmt = stmt.where(
                or_(
                    AuditLog.action.ilike(search_pattern),
                    AuditLog.module.ilike(search_pattern),
                    cast(AuditLog.ip_address, String).ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )

        result = await self.db.execute(stmt)
        return result.scalars().all()
