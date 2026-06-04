"""
notification_service.py — Real-time WebSocket notification manager.

Maintains active WebSocket connections and broadcasts JSON alerts
(e.g., 'Stock Critical', 'New Order') to connected clients.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections for real-time dashboard alerts."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept the connection and add it to the active pool."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket connection. Total active: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a connection from the pool."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected. Total active: %d", len(self.active_connections))

    async def broadcast_alert(self, title: str, message: str, level: str = "info") -> None:
        """
        Push a JSON alert to all connected clients.
        
        Args:
            title: Short alert title (e.g. "Stock Critical").
            message: Detailed message body.
            level: "info", "warning", or "error".
        """
        payload = {
            "type": "alert",
            "level": level,
            "title": title,
            "message": message,
        }
        
        # Snapshot the list to safely iterate if connections drop
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.warning("Failed to send message to websocket: %s", e)
                self.disconnect(connection)


# Global singleton instance to be imported by routes and other services
notifier = ConnectionManager()
