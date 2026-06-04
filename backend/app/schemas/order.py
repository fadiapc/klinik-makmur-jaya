"""
order.py (schemas) — Pydantic request/response models for the Orders module.

Covers:
  • CheckoutItemRequest     — one line item inside a checkout request
  • CheckoutRequest         — full checkout body (items + payment details)
  • OrderItemOut            — line-item in API response (price-snapshot safe)
  • PrescriptionOut         — prescription status embedded in OrderOut
  • OrderOut                — full order response
  • OrderStatusUpdate       — PATCH /orders/{id}/status body
  • PrescriptionReviewRequest — PATCH prescription review body (Apoteker)
  • PrescriptionUploadResponse — response after prescription image upload
"""

from __future__ import annotations

import enum
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.models import OrderStatus, OrderType, PaymentMethod, PaymentStatus, PrescriptionStatus


# ── Checkout request ──────────────────────────────────────────────────────────


class CheckoutItemRequest(BaseModel):
    """A single product line inside a checkout request."""

    product_id: int = Field(..., ge=1, description="Product ID to purchase")
    quantity: int = Field(..., ge=1, le=999, description="Number of units (max 999 per item)")


class CheckoutRequest(BaseModel):
    """
    POST /api/v1/orders/checkout

    Accepted by all roles:
      • Pasien  — places their own online order (customer_id ignored)
      • Kasir   — places a counter order; customer_id is optional
                  (no linked account = kasir's id is used as placeholder)
      • Admin   — same as Kasir
    """

    items: List[CheckoutItemRequest] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Order line items (1–50 distinct products)",
    )
    payment_method: PaymentMethod = Field(
        ...,
        description="Payment instrument: 'cash', 'transfer', or 'qris'",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Free-text notes (e.g. delivery address, special requests)",
    )
    customer_id: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "Kasir/Admin only: specify the customer (patient) user ID. "
            "Ignored when the requesting user is a Pasien."
        ),
    )

    @field_validator("items")
    @classmethod
    def no_duplicate_products(cls, v: List[CheckoutItemRequest]) -> List[CheckoutItemRequest]:
        """Prevent the same product_id appearing more than once in the request."""
        ids = [item.product_id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "Duplicate product_id found in items. "
                "Combine quantities into a single line item per product."
            )
        return v


# ── Order status update ───────────────────────────────────────────────────────


class OrderStatusUpdate(BaseModel):
    """PATCH /api/v1/orders/{id}/status — advance the order lifecycle."""

    status: OrderStatus = Field(
        ...,
        description="Target status: confirmed | processing | ready | completed | cancelled",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional note explaining the status change",
    )


# ── Prescription review ───────────────────────────────────────────────────────


class PrescriptionReviewRequest(BaseModel):
    """
    PATCH /api/v1/orders/{id}/prescription/review (Apoteker only).

    Approves or rejects an uploaded prescription.
    rejection_reason is REQUIRED when action = 'rejected'.
    """

    action: Literal["approved", "rejected"] = Field(
        ...,
        description="Pharmacist decision: 'approved' or 'rejected'",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Required when action = 'rejected'",
    )

    @model_validator(mode="after")
    def rejection_reason_required_on_reject(self) -> "PrescriptionReviewRequest":
        if self.action == "rejected" and not self.rejection_reason:
            raise ValueError(
                "rejection_reason is required when action = 'rejected'."
            )
        return self


# ── Response sub-schemas ──────────────────────────────────────────────────────


class OrderItemOut(BaseModel):
    """Line-item embedded in OrderOut."""

    id: int
    product_id: int
    product_name: str
    product_sku: str
    requires_prescription: bool
    quantity: int
    unit_price: Decimal = Field(description="Price snapshot at purchase time (IDR)")
    subtotal: Decimal = Field(description="unit_price × quantity (IDR)")

    model_config = {"from_attributes": True}


class PrescriptionOut(BaseModel):
    """Prescription record embedded in OrderOut."""

    id: int
    status: str = Field(description="pending | approved | rejected")
    image_url: str = Field(description="Relative path to prescription image")
    patient_name: str
    pharmacist_name: Optional[str] = None
    rejection_reason: Optional[str] = None
    verified_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 UTC timestamp of pharmacist review",
    )
    uploaded_at: str = Field(description="ISO-8601 UTC timestamp of initial upload")

    model_config = {"from_attributes": True}


class FifoDeductionDetail(BaseModel):
    """Internal detail of which stock batch was deducted (returned in checkout response)."""

    batch_id: int
    batch_number: str
    expiry_date: str
    quantity_deducted: int


class OrderOut(BaseModel):
    """
    Full order representation returned by all order endpoints.

    Financial values are Decimal(12,2) — never float.
    The `stock_deductions` field is only present immediately after checkout
    (removed from GET responses to keep the payload clean).
    """

    id: int
    order_code: str
    customer_name: str
    customer_email: str
    cashier_name: Optional[str] = None
    status: str
    order_type: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    grand_total: Decimal
    payment_method: str
    payment_status: str
    notes: Optional[str]
    requires_prescription: bool = Field(
        description="True if any line item is a prescription-required drug"
    )
    prescription_required_and_missing: bool = Field(
        default=False,
        description=(
            "True immediately after checkout when requires_prescription=True "
            "but no prescription has been uploaded yet. "
            "Use POST /orders/{id}/prescription to upload."
        ),
    )
    items: List[OrderItemOut]
    prescription: Optional[PrescriptionOut] = None
    stock_deductions: Optional[List[FifoDeductionDetail]] = Field(
        default=None,
        description="FIFO deduction audit trail (only on checkout response)",
    )
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PrescriptionUploadResponse(BaseModel):
    """Response after POST /api/v1/orders/{id}/prescription."""

    order_id: int
    prescription_id: int
    status: str = "pending"
    image_url: str
    message: str = (
        "Prescription uploaded successfully. "
        "An Apoteker will review your prescription and update your order status."
    )
