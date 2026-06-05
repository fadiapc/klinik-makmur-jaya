"""
notification_routes.py — REST API for managing persistent notifications.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.models import Notification, User
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/notifications", tags=["🔔 Notifications"])


@router.get("")
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all notifications for the current user, sorted by newest first.
    """
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)  # limit to last 50
    )
    notifs = result.scalars().all()
    
    # We will just return dicts so no need for explicit schemas unless necessary
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "level": n.level,
                "type": n.type,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in notifs
        ]
    }


@router.post("/{notif_id}/read", response_model=MessageResponse)
async def mark_notification_as_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Mark a specific notification as read.
    """
    result = await db.execute(
        select(Notification).where(Notification.id == notif_id, Notification.user_id == current_user.id)
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    await db.commit()
    return MessageResponse(message="Notification marked as read")


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Mark all notifications for the current user as read.
    """
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return MessageResponse(message="All notifications marked as read")
