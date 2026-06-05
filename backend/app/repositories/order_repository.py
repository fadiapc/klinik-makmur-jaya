"""
order_repository.py — Data Access Layer for orders, order_items, prescriptions,
and the FIFO stock_batches query.

Critical design principle
─────────────────────────
The FIFO stock deduction uses `SELECT ... FOR UPDATE` (pessimistic row-level
locking).  When two concurrent checkout requests try to deduct from the same
product's batches:

  Thread A → locks rows → deducts → commits → releases lock
  Thread B → waits for A's lock → then sees A's updated quantities → deducts

This prevents over-selling without requiring application-level queues.
The lock is automatically released when the transaction commits or rolls back
(which get_db() handles at the end of every request).

All methods are async and operate within a caller-supplied AsyncSession.
Business logic lives in order_service.py — this layer is pure SQL.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Order,
    OrderItem,
    OrderStatus,
    OrderType,
    PaymentMethod,
    Prescription,
    PrescriptionStatus,
    Product,
    StockBatch,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# § 1  FIFO stock-batch query
# ══════════════════════════════════════════════════════════════════════════════


class InsufficientStockError(Exception):
    """Raised when available stock < requested quantity for a product."""

    def __init__(self, product_id: int, product_name: str, requested: int, available: int) -> None:
        self.product_id = product_id
        self.product_name = product_name
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for '{product_name}' (id={product_id}): "
            f"requested={requested}, available={available}."
        )


# ══════════════════════════════════════════════════════════════════════════════
# § 2  OrderRepository
# ══════════════════════════════════════════════════════════════════════════════


class OrderRepository:
    """
    Encapsulates all database queries for orders, order_items, and prescriptions.

    Usage:
        repo = OrderRepository(db)
        order = await repo.get_by_id(42, load_related=True)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── FIFO stock deduction ──────────────────────────────────────────────────

    async def fifo_deduct_stock(
        self,
        product_id: int,
        product_name: str,
        quantity_needed: int,
    ) -> list[Tuple[StockBatch, int]]:
        """
        FIFO / FEFO stock deduction with pessimistic locking.

        Algorithm
        ─────────
        1. SELECT all batches for `product_id` with quantity > 0
           ordered by expiry_date ASC, received_at ASC
           WITH FOR UPDATE  ← row-level lock (blocks concurrent requests)
        2. Validate total available ≥ requested (fail fast, no partial deduction)
        3. Iterate batches oldest-expiry-first, deducting units until satisfied
        4. Write updated quantities back to DB via db.add(batch)
           (NOT committed yet — get_db() commits after the route handler returns)

        Returns:
            List of (StockBatch, quantity_deducted) pairs for audit trail.

        Raises:
            InsufficientStockError — if total available stock < quantity_needed
        """
        # ── Lock rows FOR UPDATE ──────────────────────────────────────────────
        result = await self.db.execute(
            select(StockBatch)
            .where(
                StockBatch.product_id == product_id,
                StockBatch.quantity > 0,
            )
            # FEFO sort: closest-expiry first, then oldest-received as tiebreaker
            .order_by(StockBatch.expiry_date.asc(), StockBatch.received_at.asc())
            .with_for_update()          # ← SELECT … FOR UPDATE (PostgreSQL row lock)
        )
        batches: list[StockBatch] = list(result.scalars().all())

        # ── Pre-check total availability (atomic — we hold the lock) ──────────
        total_available = sum(b.quantity for b in batches)
        if total_available < quantity_needed:
            raise InsufficientStockError(
                product_id=product_id,
                product_name=product_name,
                requested=quantity_needed,
                available=total_available,
            )

        # ── FIFO deduction loop ───────────────────────────────────────────────
        deductions: list[Tuple[StockBatch, int]] = []
        remaining = quantity_needed

        for batch in batches:
            if remaining <= 0:
                break
            deduct = min(batch.quantity, remaining)
            batch.quantity -= deduct
            remaining -= deduct
            self.db.add(batch)          # mark as dirty — will be flushed with order
            deductions.append((batch, deduct))
            logger.debug(
                "FIFO deduct | product_id=%d batch_id=%d batch=%s "
                "expiry=%s deducted=%d remaining_in_batch=%d",
                product_id,
                batch.id,
                batch.batch_number,
                batch.expiry_date,
                deduct,
                batch.quantity,
            )

        return deductions

    # ── Order code generation ─────────────────────────────────────────────────

    async def generate_order_code(self) -> str:
        """
        Generate a human-readable unique order code: ORD-YYYYMMDD-NNNN.

        Uses COUNT of today's orders to derive the sequence number.

        Note: In high-concurrency scenarios (> 1000 orders/day, concurrent requests),
        use a PostgreSQL SEQUENCE (CREATE SEQUENCE order_seq) instead for
        guaranteed monotonic unique numbers. For this clinic's expected volume,
        the COUNT approach is safe and simpler.
        """
        today = datetime.now(timezone.utc)
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        today_str = today_start.strftime("%Y%m%d")

        count_result = await self.db.execute(
            select(func.count(Order.id)).where(
                Order.created_at >= today_start,
                Order.created_at < tomorrow_start,
            )
        )
        sequence = (count_result.scalar_one() or 0) + 1
        return f"ORD-{today_str}-{sequence:04d}"

    # ── Product lookup ────────────────────────────────────────────────────────

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Fetch a product for checkout validation."""
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    # ── Order writes ──────────────────────────────────────────────────────────

    async def create_order(
        self,
        *,
        order_code: str,
        user_id: int,
        cashier_id: Optional[int],
        order_type: OrderType,
        payment_method: PaymentMethod,
        subtotal: Decimal,
        discount: Decimal,
        tax: Decimal,
        grand_total: Decimal,
        notes: Optional[str],
        initial_status: Optional[OrderStatus] = None,
        payment_deadline: Optional[datetime] = None,
    ) -> Order:
        """Insert the order header row and flush to get the assigned id."""
        order = Order(
            order_code=order_code,
            user_id=user_id,
            cashier_id=cashier_id,
            order_type=order_type,
            payment_method=payment_method,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            grand_total=grand_total,
            notes=notes,
        )
        if initial_status is not None:
            order.status = initial_status
        if payment_deadline is not None:
            order.payment_deadline = payment_deadline
        self.db.add(order)
        await self.db.flush()   # assigns order.id from DB IDENTITY column
        return order

    async def bulk_create_order_items(
        self,
        order_id: int,
        items: list[dict],
    ) -> list[OrderItem]:
        """
        Batch-insert all order line items in a single db.add_all() call.

        Args:
            order_id: FK to the parent order.
            items:    list of dicts with keys:
                      product_id, quantity, unit_price, subtotal
        """
        order_items = [
            OrderItem(
                order_id=order_id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["subtotal"],
            )
            for item in items
        ]
        self.db.add_all(order_items)
        await self.db.flush()
        return order_items

    # ── Order reads ───────────────────────────────────────────────────────────

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """
        Fetch a single order with all related objects eager-loaded.

        Eagerly loads: customer, cashier, items (with products), prescription.
        """
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.cashier),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.prescription),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, order_code: str) -> Optional[Order]:
        """Fetch an order by human-readable code (e.g. ORD-20250601-0001)."""
        result = await self.db.execute(
            select(Order)
            .where(Order.order_code == order_code)
            .options(
                selectinload(Order.customer),
                selectinload(Order.cashier),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.prescription),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        page: int,
        page_size: int,
        status_filter: Optional[OrderStatus] = None,
    ) -> Tuple[list[Order], int]:
        """Paginated order list for a specific customer (Pasien view)."""
        conditions = [Order.user_id == user_id]
        if status_filter:
            conditions.append(Order.status == status_filter)

        count_stmt = select(func.count(Order.id)).where(*conditions)
        total: int = (await self.db.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        data_stmt = (
            select(Order)
            .where(*conditions)
            .options(
                selectinload(Order.customer),
                selectinload(Order.cashier),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.prescription),
            )
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = (await self.db.execute(data_stmt)).scalars().all()
        return list(rows), total

    async def list_all(
        self,
        page: int,
        page_size: int,
        status_filter: Optional[OrderStatus] = None,
        user_id_filter: Optional[int] = None,
    ) -> Tuple[list[Order], int]:
        """Paginated all-orders list for Admin / Apoteker / Kasir views."""
        conditions = []
        if status_filter:
            conditions.append(Order.status == status_filter)
        if user_id_filter:
            conditions.append(Order.user_id == user_id_filter)

        count_stmt = select(func.count(Order.id)).where(*conditions)
        total: int = (await self.db.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        data_stmt = (
            select(Order)
            .where(*conditions)
            .options(
                selectinload(Order.customer),
                selectinload(Order.cashier),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.prescription),
            )
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = (await self.db.execute(data_stmt)).scalars().all()
        return list(rows), total

    async def update_status(
        self,
        order: Order,
        new_status: OrderStatus,
        notes: Optional[str] = None,
    ) -> Order:
        """Update the order lifecycle status (and optionally append a note)."""
        order.status = new_status
        if notes:
            existing = order.notes or ""
            order.notes = f"{existing}\n[{new_status.value.upper()}] {notes}".strip()
        self.db.add(order)
        await self.db.flush()
        return order

    # ── Prescription writes ───────────────────────────────────────────────────

    async def create_prescription(
        self,
        *,
        order_id: int,
        patient_id: int,
        image_url: str,
    ) -> Prescription:
        """
        Insert a new Prescription row (status = PENDING).

        The UNIQUE constraint on order_id at DB level guarantees 1:1 with Order.
        If called twice for the same order_id, PostgreSQL raises IntegrityError
        which the service layer maps to HTTP 409.
        """
        prescription = Prescription(
            order_id=order_id,
            patient_id=patient_id,
            image_url=image_url,
            status=PrescriptionStatus.PENDING,
        )
        self.db.add(prescription)
        await self.db.flush()
        return prescription

    async def update_prescription_review(
        self,
        prescription: Prescription,
        *,
        pharmacist_id: int,
        new_status: PrescriptionStatus,
        rejection_reason: Optional[str],
        reviewed_at: datetime,
    ) -> Prescription:
        """Apply Apoteker review outcome (approved / rejected)."""
        prescription.pharmacist_id = pharmacist_id
        prescription.status = new_status
        prescription.rejection_reason = rejection_reason
        prescription.verified_at = reviewed_at
        self.db.add(prescription)
        await self.db.flush()
        return prescription

    async def get_prescription_by_order_id(self, order_id: int) -> Optional[Prescription]:
        """Fetch the prescription for a given order (may be None)."""
        result = await self.db.execute(
            select(Prescription)
            .where(Prescription.order_id == order_id)
            .options(
                selectinload(Prescription.patient),
                selectinload(Prescription.pharmacist),
            )
        )
        return result.scalar_one_or_none()

    # ── Payment & Tracking updates ────────────────────────────────────────────

    async def update_payment_proof(self, order: Order, url: Optional[str]) -> Order:
        """Save or clear the customer-uploaded payment proof URL."""
        order.payment_proof_url = url
        self.db.add(order)
        await self.db.flush()
        return order

    async def update_tracking(self, order: Order, tracking_number: str) -> Order:
        """Save the courier tracking number."""
        order.tracking_number = tracking_number
        self.db.add(order)
        await self.db.flush()
        return order

    async def update_payment_deadline(self, order: Order, deadline: datetime) -> Order:
        """Set the payment deadline for auto-cancel background job."""
        order.payment_deadline = deadline
        self.db.add(order)
        await self.db.flush()
        return order

    async def list_overdue_orders(self) -> list[Order]:
        """Fetch all orders past their payment_deadline for auto-cancel job."""
        from sqlalchemy import and_
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Order)
            .where(
                and_(
                    Order.status == OrderStatus.MENUNGGU_PEMBAYARAN,
                    Order.payment_deadline != None,
                    Order.payment_deadline < now,
                )
            )
        )
        return list(result.scalars().all())
