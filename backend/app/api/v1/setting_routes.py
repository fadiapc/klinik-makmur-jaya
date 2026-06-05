from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.core.database import get_db
from app.models.models import User, SystemSetting
from app.core.dependencies import RequireAdmin
from app.schemas.setting import SettingListUpdate

router = APIRouter(tags=["Settings"])

DEFAULT_SETTINGS = {
    "ENABLE_LOW_STOCK_ALERTS": "true",
    "ENABLE_EXPIRY_ALERTS": "true",
    "EXPIRY_ALERT_DAYS": "30",
    "LOW_STOCK_ALERT_FREQ": "daily",
}

@router.get("/settings")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireAdmin),
) -> Dict[str, str]:
    """Get all system settings as key-value pairs."""
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    
    settings_dict = {s.key: s.value for s in settings}
    
    # Merge with defaults
    for key, val in DEFAULT_SETTINGS.items():
        if key not in settings_dict:
            settings_dict[key] = val
            
    return settings_dict

@router.put("/settings")
async def update_settings(
    payload: SettingListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireAdmin),
) -> Dict[str, str]:
    """Update multiple system settings."""
    for key, value in payload.settings.items():
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalars().first()
        
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSetting(key=key, value=str(value))
            db.add(setting)
            
    await db.commit()
    
    # Return updated settings
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    
    settings_dict = {s.key: s.value for s in settings}
    for key, val in DEFAULT_SETTINGS.items():
        if key not in settings_dict:
            settings_dict[key] = val
            
    return settings_dict
