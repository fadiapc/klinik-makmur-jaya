"""
notification_service.py — Real-time WebSocket notification manager with DB persistence.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.models import Notification, Role, User

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections for real-time dashboard alerts."""

    def __init__(self) -> None:
        # Maps user_id -> list of active WebSockets (user might have multiple tabs)
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Accept the connection and add it to the active pool."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"New WebSocket connection for user {user_id}. Total for user: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """Remove a connection from the pool."""
        if user_id in self.active_connections and websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}.")

    async def send_personal_alert(self, user_id: int, payload: dict) -> None:
        """Send an alert payload to a specific user's connected sockets."""
        if user_id in self.active_connections:
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(payload)
                except Exception as e:
                    logger.warning(f"Failed to send message to websocket for user {user_id}: {e}")
                    self.disconnect(connection, user_id)

    async def notify_user(
        self,
        user_id: int,
        title: str,
        message: str,
        level: str = "info",
        type: str = "system",
        link: str = None
    ) -> None:
        """
        Save notification to DB and push to user via WS if online.
        """
        # Save to DB
        async with AsyncSessionLocal() as session:
            notif = Notification(
                user_id=user_id,
                title=title,
                message=message,
                level=level,
                type=type,
                link=link
            )
            session.add(notif)
            await session.commit()
            await session.refresh(notif)

            # Push to WS
            payload = {
                "id": str(notif.id),
                "type": "alert",
                "level": level,
                "title": title,
                "message": message,
                "notif_type": type,
                "timestamp": int(notif.created_at.timestamp() * 1000)
            }
            if link:
                payload["link"] = link
            
            await self.send_personal_alert(user_id, payload)

    async def notify_role(
        self,
        role_name: str,
        title: str,
        message: str,
        level: str = "info",
        type: str = "system",
        link: str = None
    ) -> None:
        """
        Find all users with a specific role and notify each of them.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).join(Role).where(Role.name == role_name)
            )
            users = result.scalars().all()
            
            # Create a notification for each user
            notifs = [
                Notification(
                    user_id=u.id,
                    title=title,
                    message=message,
                    level=level,
                    type=type,
                    link=link
                )
                for u in users
            ]
            if notifs:
                session.add_all(notifs)
                await session.commit()
                for notif in notifs:
                    await session.refresh(notif)

        # Broadcast via WS to all users of that role
        for notif in notifs:
            payload = {
                "id": str(notif.id),
                "type": "alert",
                "level": level,
                "title": title,
                "message": message,
                "notif_type": type,
                "timestamp": int(notif.created_at.timestamp() * 1000)
            }
            if link:
                payload["link"] = link
            await self.send_personal_alert(notif.user_id, payload)

    async def broadcast_alert(self, title: str, message: str, level: str = "info", link: str = None) -> None:
        """
        Legacy method: Push a JSON alert to ALL connected clients (does not save to DB).
        """
        payload = {
            "type": "alert",
            "level": level,
            "title": title,
            "message": message,
        }
        if link:
            payload["link"] = link
        
        for user_conns in self.active_connections.values():
            for connection in list(user_conns):
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

# Global singleton instance to be imported by routes and other services
notifier = ConnectionManager()
