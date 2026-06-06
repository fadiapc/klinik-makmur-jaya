"""
apoteker_routes.py — Apoteker (Pharmacist) Dashboard API endpoints.

Provides:
  GET /api/v1/apoteker/stats          Summary stats (pending prescriptions, critical stock, near-expiry)
  GET /api/v1/apoteker/prescriptions  Pending prescription queue
  GET /api/v1/apoteker/near-expiry    Near-expiry stock batches (FIFO alert)
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import RequireAdminOrApoteker
from app.models.models import (
    Order,
    OrderItem,
    OrderStatus,
    Prescription,
    PrescriptionStatus,
    Product,
    StockBatch,
    User,
)
from app.schemas.apoteker import StockBatchCreate, StockBatchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/apoteker", tags=["💊 Apoteker Dashboard"])


# ── Pydantic response schemas ─────────────────────────────────────────────────


class ApotekerStats(BaseModel):
    pending_prescriptions: int
    critical_stock_count: int
    near_expiry_count: int


class PendingPrescriptionItem(BaseModel):
    order_id: int
    order_code: str
    customer_name: str
    drug_names: str
    image_url: str
    uploaded_at: str

    model_config = {"from_attributes": True}


class PrescriptionHistoryItem(BaseModel):
    """Full prescription history item (all statuses)."""
    prescription_id: int
    order_id: int
    order_code: str
    customer_name: str
    drug_names: str
    image_url: str
    status: str  # pending | approved | rejected
    rejection_reason: Optional[str] = None
    pharmacist_name: Optional[str] = None
    uploaded_at: str
    verified_at: Optional[str] = None

    model_config = {"from_attributes": True}


class NearExpiryItem(BaseModel):
    batch_id: int
    product_id: int
    product_name: str
    batch_number: str
    quantity_remaining: int  # will hold batch.quantity
    expiry_date: str
    days_until_expiry: int

    model_config = {"from_attributes": True}


# ── Helper ────────────────────────────────────────────────────────────────────

def _db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/stats",
    response_model=ApotekerStats,
    summary="Apoteker Dashboard Stats",
    description="Returns summary counts for the apoteker dashboard.",
)
async def get_apoteker_stats(
    current_user: User = Depends(RequireAdminOrApoteker),
    db: AsyncSession = Depends(get_db),
) -> ApotekerStats:
    """Return summary counts for apoteker dashboard."""

    # 1. Pending prescriptions
    pending_stmt = (
        select(func.count())
        .select_from(Prescription)
        .where(Prescription.status == PrescriptionStatus.PENDING)
    )
    pending_result = await db.execute(pending_stmt)
    pending_count = pending_result.scalar_one_or_none() or 0

    # 2. Critical stock (product total quantity < min_stock_threshold)
    critical_stmt2 = (
        select(func.count())
        .select_from(
            select(StockBatch.product_id)
            .join(Product, Product.id == StockBatch.product_id)
            .where(Product.is_active == True)
            .group_by(StockBatch.product_id, Product.min_stock_threshold)
            .having(func.sum(StockBatch.quantity) < Product.min_stock_threshold)
            .subquery()
        )
    )
    critical_result = await db.execute(critical_stmt2)
    critical_count = critical_result.scalar_one_or_none() or 0

    # 3. Near-expiry batches (within 90 days)
    today = date.today()
    threshold = today + timedelta(days=90)
    near_expiry_stmt = (
        select(func.count())
        .select_from(StockBatch)
        .where(
            StockBatch.quantity > 0,
            StockBatch.expiry_date != None,
            StockBatch.expiry_date <= threshold,
            StockBatch.expiry_date >= today,
        )
    )
    near_expiry_result = await db.execute(near_expiry_stmt)
    near_expiry_count = near_expiry_result.scalar_one_or_none() or 0

    return ApotekerStats(
        pending_prescriptions=pending_count,
        critical_stock_count=critical_count,
        near_expiry_count=near_expiry_count,
    )


@router.get(
    "/prescriptions",
    response_model=List[PendingPrescriptionItem],
    summary="Pending Prescription Queue",
    description="Returns orders with a PENDING prescription awaiting pharmacist review.",
)
async def get_pending_prescriptions(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(RequireAdminOrApoteker),
    db: AsyncSession = Depends(get_db),
) -> List[PendingPrescriptionItem]:
    """Fetch pending prescription queue."""

    stmt = (
        select(Prescription)
        .join(Order, Order.id == Prescription.order_id)
        .where(Prescription.status == PrescriptionStatus.PENDING)
        .options(
            selectinload(Prescription.order).selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Prescription.order).selectinload(Order.customer),
        )
        .order_by(Prescription.created_at.asc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    prescriptions = result.scalars().all()

    items: List[PendingPrescriptionItem] = []
    for p in prescriptions:
        order = p.order
        drug_names = ", ".join(
            item.product.name for item in order.items if item.product
        ) if order and order.items else "-"
        customer_name = order.customer.name if order and order.customer else "-"
        items.append(
            PendingPrescriptionItem(
                order_id=order.id,
                order_code=order.order_code,
                customer_name=customer_name,
                drug_names=drug_names,
                image_url=p.image_url,
                uploaded_at=p.created_at.isoformat() if p.created_at else "",
            )
        )
    return items


@router.get(
    "/near-expiry",
    response_model=List[NearExpiryItem],
    summary="Near-Expiry Stock Batches (FIFO Alert)",
    description="Returns stock batches expiring within 90 days, sorted soonest first.",
)
async def get_near_expiry_batches(
    days: int = Query(default=90, ge=1, le=365, description="Days threshold for expiry alert"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(RequireAdminOrApoteker),
    db: AsyncSession = Depends(get_db),
) -> List[NearExpiryItem]:
    """Return near-expiry stock batches."""

    today = date.today()
    threshold = today + timedelta(days=days)

    stmt = (
        select(StockBatch)
        .join(Product, Product.id == StockBatch.product_id)
        .where(
            StockBatch.quantity > 0,
            StockBatch.expiry_date != None,
            StockBatch.expiry_date <= threshold,
            StockBatch.expiry_date >= today,
            Product.is_active == True,
        )
        .options(selectinload(StockBatch.product))
        .order_by(StockBatch.expiry_date.asc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    batches = result.scalars().all()

    items: List[NearExpiryItem] = []
    for b in batches:
        days_left = (b.expiry_date - today).days if b.expiry_date else 0
        items.append(
            NearExpiryItem(
                batch_id=b.id,
                product_id=b.product_id,
                product_name=b.product.name if b.product else "-",
                batch_number=b.batch_number,
                quantity_remaining=b.quantity,  # actual field name in model
                expiry_date=b.expiry_date.strftime("%d %B %Y") if b.expiry_date else "-",
                days_until_expiry=days_left,
            )
        )
    return items


@router.get(
    "/prescriptions/history",
    response_model=List[PrescriptionHistoryItem],
    summary="Prescription History (All Statuses)",
    description="Returns all prescriptions with status filter, search, and pagination for the apoteker riwayat view.",
)
async def get_prescription_history(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter: pending | approved | rejected"),
    search: Optional[str] = Query(default=None, description="Search by order code or customer name"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(RequireAdminOrApoteker),
    db: AsyncSession = Depends(get_db),
) -> List[PrescriptionHistoryItem]:
    """Return all prescriptions with optional status filter and search."""
    from sqlalchemy import desc, or_, cast, String

    # Base query
    stmt = (
        select(Prescription)
        .join(Order, Order.id == Prescription.order_id)
        .options(
            selectinload(Prescription.order).selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Prescription.order).selectinload(Order.customer),
            selectinload(Prescription.pharmacist),
        )
        .order_by(desc(Prescription.created_at))
    )

    # Status filter
    if status_filter:
        try:
            status_enum = PrescriptionStatus(status_filter.lower())
            stmt = stmt.where(Prescription.status == status_enum)
        except ValueError:
            pass  # Invalid status — ignore filter

    # Search by order code or customer name
    if search:
        search_term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Order.order_code.ilike(search_term),
                Order.customer_name.ilike(search_term),
            )
        )

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    prescriptions = result.scalars().all()

    items: List[PrescriptionHistoryItem] = []
    for p in prescriptions:
        order = p.order
        drug_names = (
            ", ".join(item.product.name for item in order.items if item.product)
            if order and order.items else "-"
        )
        customer_name = (
            order.customer.name if order and order.customer
            else "-"
        )
        pharmacist_name = p.pharmacist.name if p.pharmacist else None

        items.append(
            PrescriptionHistoryItem(
                prescription_id=p.id,
                order_id=order.id,
                order_code=order.order_code,
                customer_name=customer_name,
                drug_names=drug_names,
                image_url=p.image_url,
                status=p.status.value if hasattr(p.status, "value") else str(p.status),
                rejection_reason=p.rejection_reason,
                pharmacist_name=pharmacist_name,
                uploaded_at=p.created_at.isoformat() if p.created_at else "",
            )
        )
    return items

@router.post(
    "/batches",
    response_model=StockBatchResponse,
    summary="Create a new stock batch",
    description="Allows Apoteker to receive new stock batches for a product.",
)
async def create_stock_batch(
    data: StockBatchCreate,
    current_user: User = Depends(RequireAdminOrApoteker),
    db: AsyncSession = Depends(get_db),
) -> StockBatchResponse:
    from fastapi import HTTPException
    
    # Verify product exists
    product_result = await db.execute(select(Product).where(Product.id == data.product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_batch = StockBatch(
        product_id=data.product_id,
        batch_number=data.batch_number,
        quantity=data.quantity,
        purchase_price=data.purchase_price,
        expiry_date=data.expiry_date
    )
    db.add(new_batch)
    await db.commit()
    await db.refresh(new_batch)
    
    return StockBatchResponse(
        id=new_batch.id,
        product_id=new_batch.product_id,
        product_name=product.name,
        batch_number=new_batch.batch_number,
        quantity=new_batch.quantity,
        purchase_price=new_batch.purchase_price,
        expiry_date=new_batch.expiry_date,
        received_at=new_batch.received_at.isoformat() if new_batch.received_at else ""
    )

@router.get(
    "/batches",
    response_model=List[StockBatchResponse],
    summary="List all stock batches",
    description="Returns all stock batches, optionally filtered by search.",
)
async def get_all_stock_batches(
    search: Optional[str] = Query(default=None, description="Search by product name or batch number"),
    current_user: User = Depends(RequireAdminOrApoteker),
    db: AsyncSession = Depends(get_db),
) -> List[StockBatchResponse]:
    from sqlalchemy import or_
    
    stmt = (
        select(StockBatch)
        .join(Product, Product.id == StockBatch.product_id)
        .options(selectinload(StockBatch.product))
        .order_by(StockBatch.expiry_date.asc().nulls_last())
    )
    
    if search:
        search_term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(search_term),
                StockBatch.batch_number.ilike(search_term),
            )
        )
        
    result = await db.execute(stmt)
    batches = result.scalars().all()
    
    items = []
    for b in batches:
        items.append(StockBatchResponse(
            id=b.id,
            product_id=b.product_id,
            product_name=b.product.name if b.product else "-",
            batch_number=b.batch_number,
            quantity=b.quantity,
            purchase_price=float(b.purchase_price),
            expiry_date=b.expiry_date,
            received_at=b.received_at.isoformat() if b.received_at else ""
        ))
        
    return items

