"""
order_routes.py — FastAPI router for the Orders module.

Implements checkout, FIFO stock deduction, and prescription workflows:
  POST   /api/v1/orders/checkout                     Place a new order
  GET    /api/v1/orders                              List orders (isolated by role)
  GET    /api/v1/orders/{id}                         Get single order
  PATCH  /api/v1/orders/{id}/status                  Update order lifecycle status
  POST   /api/v1/orders/{id}/prescription            Upload prescription image (1:1)
  PATCH  /api/v1/orders/{id}/prescription/review     Pharmacist review
  POST   /api/v1/orders/{id}/payment-proof           Pelanggan upload bukti transfer
  POST   /api/v1/orders/{id}/confirm-received        Pelanggan konfirmasi terima pesanan
  POST   /api/v1/orders/{id}/kasir/confirm           Kasir konfirmasi dana masuk
  POST   /api/v1/orders/{id}/kasir/reject            Kasir tolak bukti transfer
  POST   /api/v1/orders/{id}/ship                    Apoteker kirim pesanan + input resi
"""

from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    RequireAdminOrApoteker,
    RequireAdminOrKasir,
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


# ── Request schemas ────────────────────────────────────────────────────────────

class KasirRejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500,
                        description="Alasan penolakan pembayaran (min. 5 karakter)")


class ShipOrderRequest(BaseModel):
    tracking_number: str = Field(..., min_length=3, max_length=100,
                                 description="Nomor resi pengiriman dari kurir")


# ── Checkout ──────────────────────────────────────────────────────────────────


@router.post(
    "/checkout",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout cart and deduct stock via FIFO",
    description=(
        "Processes an order checkout.\n\n"
        "**Status awal**:\n"
        "• Jika ada obat keras → `menunggu_verifikasi_resep`\n"
        "• Jika semua obat bebas → `menunggu_pembayaran` (deadline 24 jam)\n\n"
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
    """Fetch order details. Pelanggan isolation enforced."""
    return await service.get_order(order_id, current_user)


# ── Status Updates ────────────────────────────────────────────────────────────


@router.patch(
    "/{order_id}/status",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Update order status (manual override)",
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
    description=(
        "Pharmacist reviews the uploaded prescription (approve/reject).\n\n"
        "**Auto-transition**:\n"
        "• Approve → order status = `menunggu_pembayaran` (deadline 24 jam)\n"
        "• Reject → order status = `dibatalkan`"
    ),
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


# ── Payment Proof ─────────────────────────────────────────────────────────────


@router.post(
    "/{order_id}/payment-proof",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Upload bukti transfer (Pelanggan)",
    description=(
        "Pelanggan mengunggah foto bukti transfer bank.\n"
        "Hanya bisa dilakukan saat status pesanan = `menunggu_pembayaran`.\n"
        "Status otomatis berubah ke `menunggu_konfirmasi_kasir` setelah upload berhasil.\n"
        "Max size: 5 MB (JPEG/PNG/WebP)."
    ),
)
async def upload_payment_proof(
    order_id: int,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Upload payment proof photo."""
    return await service.upload_payment_proof(order_id, file, current_user, request)


# ── Kasir: Konfirmasi / Tolak Pembayaran ──────────────────────────────────────


@router.post(
    "/{order_id}/kasir/confirm",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Kasir konfirmasi dana masuk (UC-K04)",
    description=(
        "Kasir mengkonfirmasi bahwa bukti transfer valid dan dana sudah masuk rekening klinik.\n"
        "Status berubah: `menunggu_konfirmasi_kasir` → `diproses`."
    ),
)
async def kasir_confirm_payment(
    order_id: int,
    request: Request,
    current_user: User = Depends(RequireAdminOrKasir),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Kasir confirms payment received."""
    return await service.kasir_confirm_payment(order_id, current_user, request)


@router.post(
    "/{order_id}/kasir/reject",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Kasir tolak bukti transfer (UC-K04 Unhappy Path)",
    description=(
        "Kasir menolak bukti transfer karena tidak valid/dana belum masuk.\n"
        "Status kembali ke `menunggu_pembayaran` agar pelanggan bisa upload ulang."
    ),
)
async def kasir_reject_payment(
    order_id: int,
    request: Request,
    data: KasirRejectRequest,
    current_user: User = Depends(RequireAdminOrKasir),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Kasir rejects payment proof."""
    return await service.kasir_reject_payment(order_id, data.reason, current_user, request)


# ── Apoteker: Kirim Pesanan ───────────────────────────────────────────────────


@router.post(
    "/{order_id}/ship",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Kirim pesanan + input resi (Apoteker, UC-A05)",
    description=(
        "Apoteker memasukkan nomor resi setelah pesanan diserahkan ke kurir.\n"
        "Status berubah: `diproses` → `dikirim`."
    ),
)
async def ship_order(
    order_id: int,
    request: Request,
    data: ShipOrderRequest,
    current_user: User = Depends(RequireAdminOrApoteker),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Apoteker ships the order with tracking number."""
    return await service.apoteker_ship_order(order_id, data.tracking_number, current_user, request)


# ── Pelanggan: Konfirmasi Diterima ────────────────────────────────────────────


@router.post(
    "/{order_id}/confirm-received",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Pelanggan konfirmasi pesanan diterima",
    description=(
        "Pelanggan mengkonfirmasi bahwa paket sudah diterima di rumah.\n"
        "Status berubah: `dikirim` → `selesai`."
    ),
)
async def confirm_received(
    order_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(_get_service),
) -> OrderOut:
    """Customer confirms order received."""
    return await service.confirm_received(order_id, current_user, request)
