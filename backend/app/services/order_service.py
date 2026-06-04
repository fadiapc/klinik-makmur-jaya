"""
order_service.py — Business logic for the Orders module.

Covers order checkout (with FIFO inventory deduction), order history retrieval,
status updates, and prescription uploads + pharmacist reviews.
"""

from __future__ import annotations

import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import (
    Order,
    OrderStatus,
    OrderType,
    PrescriptionStatus,
    User,
)
from app.repositories.order_repository import (
    InsufficientStockError,
    OrderRepository,
)
from app.schemas.common import PaginatedResponse
from app.schemas.order import (
    CheckoutRequest,
    FifoDeductionDetail,
    OrderOut,
    OrderStatusUpdate,
    PrescriptionReviewRequest,
    PrescriptionUploadResponse,
)
from app.utils.audit import log_audit

logger = logging.getLogger(__name__)

_ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
_ALLOWED_IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}


class OrderService:
    """
    Business logic for the orders module.

    Instantiate with a live AsyncSession:
        svc = OrderService(db)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = OrderRepository(db)

    # ── Checkout & FIFO ───────────────────────────────────────────────────────

    async def checkout(
        self,
        data: CheckoutRequest,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        """
        Process a new order checkout.

        Flow:
          1. Resolve customer and cashier roles.
          2. Pre-fetch and validate all requested products.
          3. Perform pessimistic FIFO stock deduction for every item.
          4. Calculate financial totals (Subtotal, 11% PPN Tax).
          5. Generate Order Code.
          6. Insert Order and OrderItems.
          7. Write Audit Log.
          8. Return OrderOut with FIFO deduction details.

        Raises:
            HTTP 400 — Insufficient stock or invalid products.
        """
        # 1. Resolve user contexts
        if current_user.role.name == "pasien":
            # Online self-checkout
            order_type = OrderType.ONLINE
            customer_id = current_user.id
            cashier_id = None
        else:
            # POS / Counter checkout
            order_type = OrderType.COUNTER
            cashier_id = current_user.id
            # Use provided customer_id, or fallback to the cashier's own ID as a placeholder
            customer_id = data.customer_id if data.customer_id else current_user.id

        # 2. Pre-fetch and validate products
        # Using a dictionary to avoid duplicate queries if they were allowed (handled by schema, but safe)
        products_map = {}
        for item in data.items:
            product = await self.repo.get_product_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id={item.product_id} not found or inactive.",
                )
            products_map[product.id] = product

        # 3. FIFO Stock Deduction & line item preparation
        subtotal = Decimal("0.00")
        line_items_data = []
        deductions_audit: list[FifoDeductionDetail] = []
        requires_rx_flag = False

        try:
            for item in data.items:
                product = products_map[item.product_id]
                
                if product.requires_prescription:
                    requires_rx_flag = True

                # Deduct stock (will raise InsufficientStockError if not enough available)
                batch_deductions = await self.repo.fifo_deduct_stock(
                    product_id=product.id,
                    product_name=product.name,
                    quantity_needed=item.quantity,
                )

                for batch, deducted_qty in batch_deductions:
                    deductions_audit.append(
                        FifoDeductionDetail(
                            batch_id=batch.id,
                            batch_number=batch.batch_number,
                            expiry_date=batch.expiry_date.isoformat(),
                            quantity_deducted=deducted_qty,
                        )
                    )

                # Prepare order item
                item_subtotal = Decimal(str(product.price)) * Decimal(item.quantity)
                subtotal += item_subtotal

                line_items_data.append({
                    "product_id": product.id,
                    "quantity": item.quantity,
                    "unit_price": Decimal(str(product.price)),
                    "subtotal": item_subtotal,
                })

        except InsufficientStockError as e:
            # Re-raise as HTTP 400. Transaction will be rolled back by `get_db`.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # 4. Financial Calculations
        discount = Decimal("0.00")  # future enhancement: promo codes
        tax_rate = Decimal("0.11")  # 11% PPN
        taxable_amount = subtotal - discount
        tax = (taxable_amount * tax_rate).quantize(Decimal("0.00"))
        grand_total = taxable_amount + tax

        # 5. Order Header
        order_code = await self.repo.generate_order_code()

        order = await self.repo.create_order(
            order_code=order_code,
            user_id=customer_id,
            cashier_id=cashier_id,
            order_type=order_type,
            payment_method=data.payment_method,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            grand_total=grand_total,
            notes=data.notes,
        )

        # 6. Order Items
        await self.repo.bulk_create_order_items(order.id, line_items_data)

        # Refresh order to fetch the relationships eagerly
        order = await self.repo.get_by_id(order.id)
        if not order:
            raise RuntimeError("Order creation failed unexpectedly.")

        # 7. Audit Log
        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="CHECKOUT_ORDER",
            module="ORDER",
            target_type="Order",
            target_id=order.id,
            new_value={
                "order_code": order_code,
                "grand_total": str(grand_total),
                "items_count": len(line_items_data),
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # 8. Build response
        order_out = OrderOut.model_validate(order)
        order_out.requires_prescription = requires_rx_flag
        order_out.prescription_required_and_missing = requires_rx_flag
        order_out.stock_deductions = deductions_audit

        logger.info(
            "Checkout successful | code=%s total=%s items=%d user_id=%d",
            order_code, str(grand_total), len(line_items_data), current_user.id
        )

        return order_out

    # ── Read Operations ───────────────────────────────────────────────────────

    async def get_order(
        self,
        order_id: int,
        current_user: User,
    ) -> OrderOut:
        """
        Fetch a single order. Pasien can only fetch their own orders.
        """
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id={order_id} not found.",
            )

        # Enforce Pasien isolation
        if current_user.role.name == "pasien" and order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this order.",
            )

        order_out = OrderOut.model_validate(order)
        # Compute dynamic flags
        requires_rx_flag = any(item.product.requires_prescription for item in order.items)
        order_out.requires_prescription = requires_rx_flag
        order_out.prescription_required_and_missing = (
            requires_rx_flag and order.prescription is None
        )

        return order_out

    async def list_orders(
        self,
        current_user: User,
        page: int,
        page_size: int,
        status_filter: Optional[OrderStatus] = None,
    ) -> PaginatedResponse[OrderOut]:
        """
        List orders. Pasien only sees their own. Admins/Staff see all.
        """
        if current_user.role.name == "pasien":
            orders, total = await self.repo.list_for_user(
                current_user.id, page, page_size, status_filter
            )
        else:
            orders, total = await self.repo.list_all(
                page, page_size, status_filter
            )

        items = []
        for o in orders:
            o_out = OrderOut.model_validate(o)
            requires_rx_flag = any(item.product.requires_prescription for item in o.items)
            o_out.requires_prescription = requires_rx_flag
            o_out.prescription_required_and_missing = (
                requires_rx_flag and o.prescription is None
            )
            items.append(o_out)

        return PaginatedResponse.build(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Status Updates ────────────────────────────────────────────────────────

    async def update_status(
        self,
        order_id: int,
        data: OrderStatusUpdate,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        """
        Advance order lifecycle status (e.g. pending -> processing).
        """
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id={order_id} not found.",
            )

        old_status = order.status
        if old_status == data.status:
            return OrderOut.model_validate(order)  # No-op

        order = await self.repo.update_status(order, data.status, data.notes)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="UPDATE_ORDER_STATUS",
            module="ORDER",
            target_type="Order",
            target_id=order.id,
            old_value={"status": old_status.value},
            new_value={"status": data.status.value, "notes": data.notes},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        logger.info(
            "Order %d status updated %s -> %s by user %d",
            order.id, old_status.value, data.status.value, current_user.id
        )

        return OrderOut.model_validate(order)

    # ── Prescriptions ─────────────────────────────────────────────────────────

    async def upload_prescription(
        self,
        order_id: int,
        file: UploadFile,
        current_user: User,
        request: Request,
    ) -> PrescriptionUploadResponse:
        """
        Upload a prescription image for a specific order.
        Strict 1:1 enforced.
        """
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id={order_id} not found.",
            )

        # Enforce Pasien isolation (only the customer can upload, unless it's staff doing it for them)
        if current_user.role.name == "pasien" and order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload prescriptions for your own orders.",
            )

        # Check if already exists (1:1 constraint)
        if order.prescription is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This order already has a prescription uploaded.",
            )

        # MIME type validation
        content_type = file.content_type or ""
        if content_type not in _ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported image type '{content_type}'. "
                    f"Allowed types: {sorted(_ALLOWED_IMAGE_TYPES)}."
                ),
            )

        # File size validation (Max 5MB for prescriptions)
        image_bytes = await file.read()
        max_bytes = 5 * 1024 * 1024
        if len(image_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Image file too large ({len(image_bytes) / 1024 / 1024:.1f} MB). "
                    f"Maximum is 5 MB."
                ),
            )

        # Build path
        ext = Path(file.filename or "").suffix.lower()
        if not ext or ext not in _ALLOWED_IMAGE_EXTENSIONS:
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            ext = ".jpg" if ext == ".jpe" else ext

        upload_root = Path(settings.UPLOAD_DIR)
        rx_dir = upload_root / "prescriptions" / str(order.id)
        rx_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}{ext}"
        file_path = rx_dir / filename

        # Write
        file_path.write_bytes(image_bytes)
        relative_url = f"prescriptions/{order.id}/{filename}"

        # DB Insert
        prescription = await self.repo.create_prescription(
            order_id=order.id,
            patient_id=current_user.id,
            image_url=relative_url,
        )

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="UPLOAD_PRESCRIPTION",
            module="ORDER",
            target_type="Prescription",
            target_id=prescription.id,
            new_value={"order_id": order.id, "image_url": relative_url},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        logger.info("Prescription uploaded for order_id=%d", order.id)

        return PrescriptionUploadResponse(
            order_id=order.id,
            prescription_id=prescription.id,
            image_url=relative_url,
        )

    async def review_prescription(
        self,
        order_id: int,
        data: PrescriptionReviewRequest,
        current_user: User,
        request: Request,
    ) -> OrderOut:
        """
        Apoteker reviews the prescription (approved/rejected).
        """
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id={order_id} not found.",
            )

        prescription = order.prescription
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No prescription found for this order.",
            )

        if prescription.status != PrescriptionStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prescription has already been {prescription.status.value}.",
            )

        new_status = (
            PrescriptionStatus.APPROVED if data.action == "approved"
            else PrescriptionStatus.REJECTED
        )

        prescription = await self.repo.update_prescription_review(
            prescription,
            pharmacist_id=current_user.id,
            new_status=new_status,
            rejection_reason=data.rejection_reason,
            reviewed_at=datetime.now(timezone.utc),
        )

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="REVIEW_PRESCRIPTION",
            module="ORDER",
            target_type="Prescription",
            target_id=prescription.id,
            new_value={"status": new_status.value, "reason": data.rejection_reason},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return OrderOut.model_validate(order)
