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
from app.models.models import Order, OrderItem, User, Product, Role, OrderStatus, Prescription
from app.repositories.user_repository import UserRepository
from app.schemas.common import MessageResponse
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.order import OrderOut
from app.services.notification_service import notifier
from app.services.report_generator import generate_pdf_report, generate_excel_report

logger = logging.getLogger(__name__)

# Two routers: one for standard REST API under /api/v1/dashboard, and one for WebSockets at /ws
router = APIRouter(prefix="/dashboard", tags=["📊 Dashboard & Reporting"])
ws_router = APIRouter(tags=["🔔 Real-time Alerts"])

# ── Background Task Logic ─────────────────────────────────────────────────────


async def _generate_sales_report(
    start_date: Optional[datetime], 
    end_date: Optional[datetime], 
    user_id: int,
    report_format: str
) -> None:
    """
    Background task to generate a sales report.
    Generates a PDF or Excel file using fpdf2 or openpyxl.
    """
    logger.info("Starting background report generation (%s) for user_id=%d", report_format, user_id)
    
    async with AsyncSessionLocal() as session:
        try:
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
            
            report_dir = Path(settings.UPLOAD_DIR) / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            if report_format == "excel":
                file_path = generate_excel_report(orders, report_dir)
            else:
                file_path = generate_pdf_report(orders, report_dir)
                
            filename = file_path.name
            logger.info("Report generation complete. Saved to %s", file_path)
            
            await notifier.broadcast_alert(
                title="Laporan Selesai",
                message=f"Laporan Penjualan ({report_format.upper()}) Anda sudah siap diunduh.",
                level="success",
                link=f"/static/reports/{filename}"
            )
            
        except Exception as e:
            logger.exception("Failed to generate background report")
            await notifier.broadcast_alert(
                title="Report Failed",
                message="An error occurred while generating the sales report.",
                level="error"
            )


# ── REST Endpoints ────────────────────────────────────────────────────────────


@router.get(
    "/reports/sales",
    response_model=MessageResponse,
    summary="Generate Sales Report (PDF or Excel)",
    description="Triggers a background task to generate a sales report for the given date range.",
)
async def generate_sales_report_endpoint(
    background_tasks: BackgroundTasks,
    format: str = Query("pdf", description="Report format: 'pdf' or 'excel'"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO8601)"),
    current_user: User = Depends(RequireAdminOrApoteker),
) -> MessageResponse:
    """Enqueues the report generation task."""
    background_tasks.add_task(_generate_sales_report, start_date, end_date, current_user.id, format.lower())
    return MessageResponse(
        message="Sales report generation started in the background. You will receive an alert when it's ready."
    )


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get Dashboard Statistics",
    description="Returns aggregate statistics for the dashboard, including a 30-day sales chart and 10 recent orders.",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireAdminOrApoteker),
) -> DashboardStatsResponse:
    from datetime import timedelta
    from sqlalchemy import func
    
    # 1. Total Products
    total_products = await db.scalar(select(func.count(Product.id)).where(Product.is_active == True))
    
    # 2. Active Orders (not selesai, not dibatalkan)
    active_orders = await db.scalar(
        select(func.count(Order.id)).where(
            Order.status.notin_([OrderStatus.SELESAI, OrderStatus.DIBATALKAN])
        )
    )
    
    # 3. Total Patients
    total_patients = await db.scalar(
        select(func.count(User.id)).join(Role).where(Role.name == "pasien")
    )
    
    # 4. Recent Orders (Top 10)
    recent_orders_stmt = (
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.cashier),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.prescription).selectinload(Prescription.patient),
            selectinload(Order.prescription).selectinload(Prescription.pharmacist)
        )
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    recent_orders_result = await db.execute(recent_orders_stmt)
    recent_orders_db = recent_orders_result.scalars().all()
    recent_orders_out = [
        OrderOut.from_orm_model(o, requires_prescription=any(item.product.requires_prescription for item in o.items))
        for o in recent_orders_db
    ]
    
    # 5. Sales Chart (Last 30 Days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    sales_stmt = (
        select(
            func.date_trunc('day', Order.created_at).label("day"),
            func.sum(Order.grand_total).label("total")
        )
        .where(Order.status == OrderStatus.SELESAI)
        .where(Order.created_at >= thirty_days_ago)
        .group_by("day")
        .order_by("day")
    )
    
    sales_result = await db.execute(sales_stmt)
    sales_data = sales_result.all()
    
    # Format to list of {"date": "YYYY-MM-DD", "total_sales": ...}
    sales_chart = []
    # Create a map for fast lookup
    sales_map = {row.day.strftime("%Y-%m-%d"): float(row.total) for row in sales_data if row.day}
    
    # Fill in the blanks for the last 30 days so the chart doesn't have gaps
    for i in range(30, -1, -1):
        day_date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        sales_chart.append({
            "date": day_date,
            "total_sales": sales_map.get(day_date, 0.0)
        })
        
    return DashboardStatsResponse(
        total_products=total_products or 0,
        active_orders=active_orders or 0,
        total_patients=total_patients or 0,
        system_health="99.9%",
        recent_orders=recent_orders_out,
        sales_chart=sales_chart
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

    await notifier.connect(websocket, user.id)
    try:
        # Keep connection open and listen for potential incoming client messages
        # In a purely one-way push system, we just loop and wait.
        while True:
            # We wait for messages but don't strictly do anything with them right now
            data = await websocket.receive_text()
            logger.debug("Received WS message from user %d: %s", user.id, data)
    except WebSocketDisconnect:
        notifier.disconnect(websocket, user.id)
