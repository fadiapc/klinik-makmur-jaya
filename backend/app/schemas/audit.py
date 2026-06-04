from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuthStats(BaseModel):
    total_logins_today: int
    successful_logins: int
    failed_logins: int


class HourlyActivity(BaseModel):
    hour: str  # Format: "00:00", "01:00", etc.
    success: int
    failed: int


class AuthorizationStats(BaseModel):
    authorized_all: int
    rbac: int
    obac: int


class DashboardStatsOut(BaseModel):
    auth_stats: AuthStats
    hourly_activity: list[HourlyActivity]
    authorization_stats: AuthorizationStats


class AuditLogOut(BaseModel):
    id: int
    created_at: datetime
    email: str
    role_name: str
    action: str
    module: str
    ip_address: Optional[str]
    status: str

    model_config = ConfigDict(from_attributes=True)
