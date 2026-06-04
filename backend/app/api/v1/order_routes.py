"""
order_routes.py — FastAPI router for the Orders module.

Implements checkout, FIFO stock deduction, and prescription workflows:
  POST   /api/v1/orders/checkout             Place a new order
  GET    /api/v1/orders                      List orders (isolated by role)
  GET    /api/v1/orders/{id}                 Get single order
  PATCH  /api/v1/orders/{id}/status          Update order lifecycle status
  POST   /api/v1/orders/{id}/prescription    Upload prescription image (1:1)
  PATCH  /api/v1/orders/{id}/prescription/review  Pharmacist review
"""

from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    RequireAdminOrApoteker,
    RequireApoteker,
    RequireStaff,
    get_current_active_user,
)
from app.models.models import OrderStatus, User
from app.schemas.common import PaginatedResponse
from app.schemas.order import (
    CheckoutRequest,
    OrderOut,
    OrderStatusUpdate,
    PrescriptionReviewRequest,
    PrescriptionUploadResponse,
)
from app.services.order_service import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["🛒 Orders & Prescriptions"],
)


def _get_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(db)


# ── Checkout ──────────────────────────────────────────────────────────────────


@router.post(
    "/checkout",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout cart and deduct stock via FIFO",
    description=(
        "Processes an order checkout.\n\n"
        "**Features**:\n"
        "1. Deducts inventory using a pessimistic FIFO lock (closest expiry first).\n"
        "2. Fails atomically if stock is insufficient.\n"
        "3. Flags the response if any item requires a prescription.\n\n"
        "**Role Behavior**:\n"
        "• `Pasien`: Order placed as online. `customer_id` is ignored.\n"
        "• `Kasir/Admin`: Order placed as counter. Provide `customer_id` if known."
    ),
)
async def checkout(
    request: Request,
    data: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Process a new order checkout (all roles allowed)."""
    return await service.checkout(data, current_user, request)


# ── Read Orders ───────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=PaginatedResponse[OrderOut],
    status_code=status.HTTP_200_OK,
    summary="List orders",
    description=(
        "List orders with pagination.\n\n"
        "• `Pasien`: Only sees their own orders.\n"
        "• `Staff`: Sees all orders across the clinic."
    ),
)
async def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[OrderStatus] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(_get_service),
) -> PaginatedResponse[OrderOut]:
    """List paginated orders."""
    return await service.list_orders(current_user, page, page_size, status_filter)


@router.get(
    "/{order_id}",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Get single order",
)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Fetch order details. Pasien isolation enforced."""
    return await service.get_order(order_id, current_user)


# ── Status Updates ────────────────────────────────────────────────────────────


@router.patch(
    "/{order_id}/status",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Update order status",
    description="Advance the lifecycle of an order. **Requires role:** Admin, Apoteker, or Kasir.",
)
async def update_order_status(
    order_id: int,
    request: Request,
    data: OrderStatusUpdate,
    current_user: User = Depends(RequireStaff),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Update order lifecycle status."""
    return await service.update_status(order_id, data, current_user, request)


# ── Prescriptions ─────────────────────────────────────────────────────────────


@router.post(
    "/{order_id}/prescription",
    response_model=PrescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload prescription photo",
    description=(
        "Upload a digital prescription for an order.\n"
        "Strict 1:1 relation: fails if a prescription already exists for this order.\n"
        "Max size: 5 MB (JPEG/PNG/WebP)."
    ),
)
async def upload_prescription(
    order_id: int,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(_get_service),
) -> PrescriptionUploadResponse:
    """Upload a prescription image for an order."""
    return await service.upload_prescription(order_id, file, current_user, request)


@router.patch(
    "/{order_id}/prescription/review",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Review prescription (Apoteker only)",
    description="Pharmacist reviews the uploaded prescription (approve/reject).",
)
async def review_prescription(
    order_id: int,
    request: Request,
    data: PrescriptionReviewRequest,
    current_user: User = Depends(RequireApoteker),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Pharmacist approves or rejects a prescription."""
    return await service.review_prescription(order_id, data, current_user, request)
