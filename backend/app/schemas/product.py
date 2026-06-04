"""
product.py (schemas) — Pydantic request/response models for the products module.

Covers:
  • ProductCreate      — POST /products body
  • ProductUpdate      — PUT /products/{id} body (all fields optional)
  • ProductOut         — safe API response (embeds category & supplier names)
  • ProductFilterParams— query string parameters for the list endpoint
  • BatchImportResponse— immediate response after POST /products/batch-import
  • ImportJobStatus    — GET /products/import-status/{job_id} response
  • ImageUploadResponse— response after POST /products/{id}/image
"""

from __future__ import annotations

import enum
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import SortOrder


# ── Allowed sort fields ───────────────────────────────────────────────────────


class ProductSortField(str, enum.Enum):
    NAME = "name"
    PRICE = "price"
    SKU = "sku"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# ── Embedded sub-schemas ──────────────────────────────────────────────────────


class CategoryBrief(BaseModel):
    """Minimal category info embedded in ProductOut."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class SupplierBrief(BaseModel):
    """Minimal supplier info embedded in ProductOut."""

    id: int
    name: str

    model_config = {"from_attributes": True}


# ── Input schemas ─────────────────────────────────────────────────────────────


class ProductCreate(BaseModel):
    """
    POST /api/v1/products — Create a new drug/product entry.

    All non-optional fields must be provided.
    """

    sku: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["OBT-AMX-500"],
        description="Globally unique Stock Keeping Unit code",
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        examples=["Amoxicillin 500mg"],
        description="Drug / product name",
    )
    category_id: int = Field(
        ...,
        ge=1,
        description="FK → categories.id",
    )
    supplier_id: int = Field(
        ...,
        ge=1,
        description="FK → suppliers.id",
    )
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        examples=[15000.00],
        description="Retail selling price per unit (IDR). Must be > 0.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="General product description",
    )
    composition: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Active ingredient composition",
    )
    dosage: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Dosage instructions",
    )
    side_effects: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Known side effects",
    )
    requires_prescription: bool = Field(
        default=False,
        description="True if this is a prescription-only drug (obat keras)",
    )
    min_stock_threshold: int = Field(
        default=10,
        ge=0,
        description="Minimum stock level before NOTIF-01 low-stock alert fires",
    )

    @field_validator("sku")
    @classmethod
    def sku_uppercase(cls, v: str) -> str:
        """Normalise SKU to uppercase for consistent storage and lookup."""
        return v.strip().upper()

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        return v.strip()


class ProductUpdate(BaseModel):
    """
    PUT /api/v1/products/{id} — Partial update.

    Every field is optional — only supplied fields are applied.
    """

    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    category_id: Optional[int] = Field(default=None, ge=1)
    supplier_id: Optional[int] = Field(default=None, ge=1)
    price: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=5000)
    composition: Optional[str] = Field(default=None, max_length=2000)
    dosage: Optional[str] = Field(default=None, max_length=2000)
    side_effects: Optional[str] = Field(default=None, max_length=2000)
    requires_prescription: Optional[bool] = None
    min_stock_threshold: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None

    model_config = {"extra": "forbid"}  # reject unknown fields explicitly


# ── Response schemas ──────────────────────────────────────────────────────────


class ProductOut(BaseModel):
    """
    Full product representation returned by all product endpoints.

    Uses the integer `id` as the public identifier (products have no UUID
    column — the sequential id is safe to expose in catalogue contexts).
    `image_url` is stored as a relative path; the frontend prefixes the
    static file server base URL.
    """

    id: int
    sku: str
    name: str
    category: CategoryBrief
    supplier: SupplierBrief
    description: Optional[str]
    composition: Optional[str]
    dosage: Optional[str]
    side_effects: Optional[str]
    price: Decimal
    requires_prescription: bool
    min_stock_threshold: int
    image_url: Optional[str] = Field(
        default=None,
        description="Relative path to product image, served at /static/<path>",
    )
    is_active: bool
    created_at: str = Field(description="ISO-8601 UTC timestamp")
    updated_at: str = Field(description="ISO-8601 UTC timestamp")

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, product: object) -> "ProductOut":
        """Build from ORM model, converting datetime fields to ISO-8601 strings."""
        from app.models.models import Product as ProductModel

        p: ProductModel = product  # type: ignore[assignment]
        return cls(
            id=p.id,
            sku=p.sku,
            name=p.name,
            category=CategoryBrief.model_validate(p.category),
            supplier=SupplierBrief.model_validate(p.supplier),
            description=p.description,
            composition=p.composition,
            dosage=p.dosage,
            side_effects=p.side_effects,
            price=p.price,
            requires_prescription=p.requires_prescription,
            min_stock_threshold=p.min_stock_threshold,
            image_url=p.image_url,
            is_active=p.is_active,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )


# ── Filter / query params ─────────────────────────────────────────────────────


class ProductFilterParams(BaseModel):
    """
    Query string parameters for GET /api/v1/products.

    All filters are optional — omit to return all active products.

    Usage (FastAPI auto-parses from query string via Depends):
        @router.get("/products")
        async def list_products(filters: ProductFilterParams = Depends()):
            ...
    """

    q: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Search term — matched against name, SKU, and description (case-insensitive)",
    )
    category_id: Optional[int] = Field(default=None, ge=1)
    supplier_id: Optional[int] = Field(default=None, ge=1)
    requires_prescription: Optional[bool] = Field(
        default=None,
        description="Filter by prescription requirement (omit for all)",
    )
    min_price: Optional[Decimal] = Field(default=None, ge=0)
    max_price: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = Field(
        default=True,
        description="Filter by active status (default: True)",
    )
    sort_by: ProductSortField = Field(
        default=ProductSortField.NAME,
        description="Column to sort by",
    )
    sort_order: SortOrder = Field(
        default=SortOrder.ASC,
        description="Sort direction",
    )


# ── Batch import schemas ──────────────────────────────────────────────────────


class BatchImportResponse(BaseModel):
    """
    Immediate response returned after POST /api/v1/products/batch-import.

    The actual processing happens in a background task.
    Poll GET /api/v1/products/import-status/{job_id} for results.
    """

    job_id: str = Field(description="UUID identifying this import job")
    message: str = Field(
        default="CSV import started. Poll import-status/{job_id} for progress."
    )
    filename: str


class ImportRowError(BaseModel):
    """A single row-level validation or insertion error during CSV import."""

    row: int = Field(description="1-based row number in the CSV (excluding header)")
    sku: Optional[str] = None
    error: str


class ImportJobStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJobStatusResponse(BaseModel):
    """
    Response for GET /api/v1/products/import-status/{job_id}.

    Reflects real-time progress while status == 'processing' and the
    final summary once status == 'completed' or 'failed'.
    """

    job_id: str
    filename: str
    status: ImportJobStatusEnum
    total_rows: int = 0
    successful: int = 0
    failed: int = 0
    errors: List[ImportRowError] = Field(default_factory=list)
    created_at: str
    completed_at: Optional[str] = None
    fatal_error: Optional[str] = Field(
        default=None,
        description="Set when the entire job fails (e.g. invalid CSV format)",
    )


# ── Image upload ──────────────────────────────────────────────────────────────


class ImageUploadResponse(BaseModel):
    """Response after a successful product image upload."""

    product_id: int
    image_url: str = Field(description="Relative storage path, served at /static/<path>")
    message: str = "Image uploaded and product record updated successfully."
