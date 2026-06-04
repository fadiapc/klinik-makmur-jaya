"""
dashboard_routes.py — Dashboard, real-time alerts, and background reporting.

Provides:
  • GET /api/v1/dashboard/reports/sales-pdf — Generates a background sales report.
  • WS /ws/alerts — Real-time WebSocket alerts (e.g., Stock Critical).
"""

from __future__ import annotations

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_db
from app.core.dependencies import RequireAdminOrApoteker, get_current_active_user
from app.core.security import decode_access_token
from app.models.models import Order, OrderItem, User
from app.repositories.user_repository import UserRepository
from app.schemas.common import MessageResponse
from app.services.notification_service import notifier

logger = logging.getLogger(__name__)

# Two routers: one for standard REST API under /api/v1/dashboard, and one for WebSockets at /ws
router = APIRouter(prefix="/dashboard", tags=["📊 Dashboard & Reporting"])
ws_router = APIRouter(tags=["🔔 Real-time Alerts"])

# ── Background Task Logic ─────────────────────────────────────────────────────


async def _generate_sales_report(start_date: Optional[datetime], end_date: Optional[datetime], user_id: int) -> None:
    """
    Background task to generate a sales report.
    For this demo, we generate a CSV file to simulate the PDF report generation,
    ensuring zero external binary dependencies (like wkhtmltopdf) so the demo runs flawlessly.
    """
    logger.info("Starting background report generation for user_id=%d", user_id)
    
    # 1. Create a fresh DB session for the background task
    async with AsyncSessionLocal() as session:
        try:
            # 2. Build the query
            conditions = []
            if start_date:
                conditions.append(Order.created_at >= start_date)
            if end_date:
                conditions.append(Order.created_at <= end_date)
            
            stmt = (
                select(Order)
                .where(*conditions)
                .options(
                    selectinload(Order.customer),
                    selectinload(Order.items).selectinload(OrderItem.product)
                )
                .order_by(Order.created_at.asc())
            )
            
            result = await session.execute(stmt)
            orders = result.scalars().all()
            
            # 3. Create the reports directory
            report_dir = Path(settings.UPLOAD_DIR) / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            # 4. Write CSV
            filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = report_dir / filename
            
            # We use synchronous file writing here, which is fine for a lightweight background task
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Order Code", "Date", "Customer", "Order Type", 
                    "Status", "Payment Method", "Grand Total (IDR)", "Items count"
                ])
                
                total_revenue = 0.0
                for order in orders:
                    writer.writerow([
                        order.order_code,
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        order.customer.full_name,
                        order.order_type.value,
                        order.status.value,
                        order.payment_method.value,
                        float(order.grand_total),
                        len(order.items)
                    ])
                    total_revenue += float(order.grand_total)
                    
                writer.writerow([])
                writer.writerow(["", "", "", "", "", "Total Revenue", total_revenue, ""])
                
            logger.info("Report generation complete. Saved to %s", file_path)
            
            # Optional: Simulate sending a WebSocket alert to the user who requested it
            await notifier.broadcast_alert(
                title="Report Ready",
                message=f"Your sales report ({filename}) is ready for download.",
                level="success"
            )
            
        except Exception as e:
            logger.error("Failed to generate background report: %s", e)
            await notifier.broadcast_alert(
                title="Report Failed",
                message="An error occurred while generating the sales report.",
                level="error"
            )


# ── REST Endpoints ────────────────────────────────────────────────────────────


@router.get(
    "/reports/sales-pdf",
    response_model=MessageResponse,
    summary="Generate Sales Report (Simulated PDF as CSV)",
    description=(
        "Triggers a background task to generate a sales report for the given date range.\n\n"
        "**Note**: For the purpose of the demo and zero-configuration environment stability, "
        "this generates a formatted `.csv` file locally rather than a PDF, avoiding the need "
        "for system-level `wkhtmltopdf` binaries. The file is saved in the `uploads/reports/` directory."
    ),
)
async def generate_sales_report_endpoint(
    background_tasks: BackgroundTasks,
    start_date: Optional[datetime] = Query(None, description="Start date (ISO8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO8601)"),
    current_user: User = Depends(RequireAdminOrApoteker),
) -> MessageResponse:
    """Enqueues the report generation task."""
    background_tasks.add_task(_generate_sales_report, start_date, end_date, current_user.id)
    return MessageResponse(
        message="Sales report generation started in the background. You will receive an alert when it's ready."
    )


# ── WebSocket Endpoints ───────────────────────────────────────────────────────


async def _get_ws_user(websocket: WebSocket, token: Optional[str]) -> Optional[User]:
    """Manually decode and fetch the user for WebSocket connections."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("uid")
        if not user_id:
            return None
        
        # We must manually manage the session here since Depends(get_db) 
        # behaves differently inside WebSockets in some FastAPI versions.
        async with AsyncSessionLocal() as db:
            repo = UserRepository(db)
            user = await repo.get_by_id(user_id)
            return user
    except Exception:
        return None


@ws_router.websocket("/ws/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None, description="JWT Bearer token"),
):
    """
    Real-time WebSocket endpoint for receiving JSON alerts.
    Pass the JWT token as a query parameter: `ws://host/ws/alerts?token=ey...`
    
    Alert format:
    ```json
    {
      "type": "alert",
      "level": "info|warning|error|success",
      "title": "Alert Title",
      "message": "Detailed message"
    }
    ```
    """
    user = await _get_ws_user(websocket, token)
    if not user:
        # Reject unauthenticated connections immediately
        await websocket.close(code=1008, reason="Unauthorized or missing token")
        return

    await notifier.connect(websocket)
    try:
        # Keep connection open and listen for potential incoming client messages
        # In a purely one-way push system, we just loop and wait.
        while True:
            # We wait for messages but don't strictly do anything with them right now
            data = await websocket.receive_text()
            logger.debug("Received WS message from user %d: %s", user.id, data)
    except WebSocketDisconnect:
        notifier.disconnect(websocket)
