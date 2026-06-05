"""
product_routes.py — FastAPI router for the Products management module.

Implements PRD Sections 4.3 (CRUD-01 through CRUD-05) and 4.5 (PAR-01, PAR-02):

  GET    /api/v1/products                   List products (paginated + filtered + sorted)
  POST   /api/v1/products                   Create a single product
  GET    /api/v1/products/{id}              Get a product by ID
  PUT    /api/v1/products/{id}              Update a product (partial)
  DELETE /api/v1/products/{id}              Soft-delete a product

  POST   /api/v1/products/batch-import      Upload CSV → background import (PAR-02)
  GET    /api/v1/products/import-status/{job_id}  Poll import job status

  POST   /api/v1/products/{id}/image        Upload product image (DASH-04)

RBAC:
  • GET endpoints           — any authenticated user (all roles)
  • POST / PUT              — Admin or Apoteker
  • DELETE                  — Admin only
  • batch-import            — Admin only
  • image upload            — Admin or Apoteker

NOTE: /batch-import and /import-status/{job_id} must be defined BEFORE
/{id} in the router to prevent FastAPI from matching "batch-import" or
"import-status" as a product ID.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    RequireAdmin,
    RequireAdminOrApoteker,
    get_current_active_user,
)
from app.models.models import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.product import (
    BatchImportResponse,
    ImageUploadResponse,
    ImportJobStatusResponse,
    ProductCreate,
    ProductFilterParams,
    ProductOut,
    ProductSortField,
    ProductUpdate,
)
from app.schemas.common import SortOrder
from app.services.product_service import (
    ProductService,
    _execute_csv_import,
    import_job_store,
)

logger = logging.getLogger(__name__)

# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/products",
    tags=["📦 Products"],
)


# ── Dependency: build ProductService from session ──────────────────────────────

def _get_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(db)


# ══════════════════════════════════════════════════════════════════════════════
# IMPORTANT: Static-path routes must come BEFORE /{id} parameterised routes
# to prevent FastAPI from interpreting "batch-import" as a product ID integer.
# ══════════════════════════════════════════════════════════════════════════════


# ── POST /products — Create product ──────────────────────────────────────────

@router.get(
    "/categories",
    response_model=list[dict],
    summary="Get all categories",
)
async def get_categories(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.models import Category
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in categories]


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (CRUD-01)",
    description=(
        "Add a drug/product to the catalogue. Validates SKU uniqueness and "
        "confirms that category and supplier IDs exist. "
        "**Requires role:** Admin or Apoteker."
    ),
    responses={
        201: {"description": "Product created successfully"},
        404: {"description": "Category or supplier not found"},
        409: {"description": "SKU already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_product(
    request: Request,
    data: ProductCreate,
    current_user: User = Depends(RequireAdminOrApoteker),
    service: ProductService = Depends(_get_service),
) -> ProductOut:
    """Create a single drug/product catalogue entry."""
    return await service.create_product(data, current_user, request)


# ── GET /products — List products (paginated + filtered) ──────────────────────


@router.get(
    "",
    response_model=PaginatedResponse[ProductOut],
    status_code=status.HTTP_200_OK,
    summary="List products with pagination, search, and filters (CRUD-05)",
    description=(
        "Returns a paginated product catalogue. All query parameters are optional.\n\n"
        "**Search (`q`)**: case-insensitive match on product name, SKU, and description.\n\n"
        "**Performance**: response time target < 500ms as per PRD CRUD-05. "
        "Results include category and supplier names (no extra round-trips).\n\n"
        "**Public endpoint**: any authenticated user may access the product catalogue."
    ),
)
async def list_products(
    # Pagination
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    # Search
    q: Optional[str] = Query(default=None, max_length=200, description="Search query"),
    # Filters
    category_id: Optional[int] = Query(default=None, ge=1),
    supplier_id: Optional[int] = Query(default=None, ge=1),
    requires_prescription: Optional[bool] = Query(default=None),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    is_active: Optional[bool] = Query(default=True),
    # Sorting
    sort_by: ProductSortField = Query(default=ProductSortField.NAME),
    sort_order: SortOrder = Query(default=SortOrder.ASC),
    service: ProductService = Depends(_get_service),
) -> PaginatedResponse[ProductOut]:
    """Paginated, filterable, sortable product list."""
    from decimal import Decimal

    filters = ProductFilterParams(
        q=q,
        category_id=category_id,
        supplier_id=supplier_id,
        requires_prescription=requires_prescription,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await service.list_products(filters, page, page_size)


# ── POST /products/batch-import — Parallel CSV import (PAR-02) ───────────────


@router.post(
    "/batch-import",
    response_model=BatchImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch import products from CSV (PAR-02 Parallel Processing)",
    description=(
        "Upload a CSV file to bulk-import products. The response is returned **immediately** "
        "(HTTP 202 Accepted) without waiting for processing to complete.\n\n"
        "**Background processing** (PAR-01/PAR-02):\n"
        "The CSV is parsed with pandas and rows are inserted in a background task "
        "after the response is sent — the API never blocks.\n\n"
        "**CSV format — required columns:**\n"
        "```\n"
        "sku,name,category_id,supplier_id,price\n"
        "OBT-AMX-500,Amoxicillin 500mg,1,1,15000\n"
        "```\n\n"
        "**Optional columns:** "
        "description, composition, dosage, side_effects, "
        "requires_prescription (true/false), min_stock_threshold, image_url\n\n"
        "**Poll status:** `GET /api/v1/products/import-status/{job_id}`\n\n"
        "**Requires role:** Admin."
    ),
    responses={
        202: {"description": "Import job accepted — processing in background"},
        400: {"description": "Not a CSV file, empty file, or file too large (> 10 MB)"},
        403: {"description": "Insufficient role"},
    },
)
async def batch_import_products(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ...,
        description=(
            "CSV file to import. Max size: 10 MB. "
            "Content-Type must be text/csv or application/csv."
        ),
    ),
    current_user: User = Depends(RequireAdmin),
    service: ProductService = Depends(_get_service),
) -> BatchImportResponse:
    """
    Receive a CSV file, register an import job, return 202 immediately.

    The actual CSV parsing and DB insertion runs as a FastAPI BackgroundTask,
    which executes after the HTTP response is sent — no blocking, no timeout.
    """
    # Validate and register the job (raises HTTP 400 on invalid file)
    response = await service.start_batch_import(file, current_user)

    # Retrieve the params stored during start_batch_import
    job_id, csv_bytes, user_id = service.get_pending_import_params()

    # Enqueue the background task — runs AFTER response is sent
    background_tasks.add_task(
        _execute_csv_import,
        job_id,
        csv_bytes,
        user_id,
    )

    logger.info(
        "Batch import job %s enqueued | user_id=%d file_size=%d bytes",
        job_id,
        current_user.id,
        len(csv_bytes),
    )
    return response


# ── GET /products/import-status/{job_id} — Poll import status ────────────────


@router.get(
    "/import-status/{job_id}",
    response_model=ImportJobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll batch import job status (PAR-02)",
    description=(
        "Check the progress and result of a batch import job. "
        "Poll this endpoint until `status` is `completed` or `failed`.\n\n"
        "**Requires role:** Admin."
    ),
    responses={
        200: {"description": "Job status (pending | processing | completed | failed)"},
        404: {"description": "Job ID not found (expired or invalid)"},
    },
)
async def get_import_status(
    job_id: str,
    current_user: User = Depends(RequireAdmin),
) -> ImportJobStatusResponse:
    """Return the current status and error details of a CSV import job."""
    return await ProductService.get_import_job_status(job_id)


# ── GET /products/{id} — Get single product ───────────────────────────────────


@router.get(
    "/{product_id}",
    response_model=ProductOut,
    status_code=status.HTTP_200_OK,
    summary="Get a single product by ID",
    description=(
        "Returns full product details including category and supplier names. "
        "Accessible by all authenticated roles."
    ),
    responses={
        200: {"description": "Product details"},
        404: {"description": "Product not found"},
    },
)
async def get_product(
    product_id: int,
    service: ProductService = Depends(_get_service),
) -> ProductOut:
    """Fetch a single product with all pharmaceutical details."""
    return await service.get_product(product_id)


# ── PUT /products/{id} — Update product ──────────────────────────────────────


@router.put(
    "/{product_id}",
    response_model=ProductOut,
    status_code=status.HTTP_200_OK,
    summary="Update a product (CRUD-01)",
    description=(
        "Partially update a product. Only include the fields you want to change — "
        "omitted fields retain their current values.\n\n"
        "**Requires role:** Admin or Apoteker."
    ),
    responses={
        200: {"description": "Updated product"},
        404: {"description": "Product, category, or supplier not found"},
        422: {"description": "Validation error"},
    },
)
async def update_product(
    product_id: int,
    request: Request,
    data: ProductUpdate,
    current_user: User = Depends(RequireAdminOrApoteker),
    service: ProductService = Depends(_get_service),
) -> ProductOut:
    """Apply a partial update to a product."""
    return await service.update_product(product_id, data, current_user, request)


# ── DELETE /products/{id} — Soft delete ──────────────────────────────────────


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a product (CRUD-01)",
    description=(
        "Marks the product as inactive (`is_active=False`). "
        "The record is preserved in the database for historical order data. "
        "**Requires role:** Admin only."
    ),
    responses={
        200: {"description": "Product deactivated"},
        404: {"description": "Product not found"},
        409: {"description": "Product already inactive"},
    },
)
async def delete_product(
    product_id: int,
    request: Request,
    current_user: User = Depends(RequireAdmin),
    service: ProductService = Depends(_get_service),
) -> MessageResponse:
    """Soft-delete a product (preserves all historical order data)."""
    await service.delete_product(product_id, current_user, request)
    return MessageResponse(
        message=f"Product id={product_id} has been deactivated successfully."
    )


# ── POST /products/{id}/image — Image upload (DASH-04) ───────────────────────


@router.post(
    "/{product_id}/image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload product image (DASH-04)",
    description=(
        "Upload a product photo. Replaces any existing image.\n\n"
        "**Accepted formats:** JPEG, PNG, WebP\n\n"
        "**Max size:** configurable via `MAX_UPLOAD_SIZE_MB` setting (default 2 MB)\n\n"
        "The image is saved to `{UPLOAD_DIR}/products/{id}/{uuid}.{ext}` and "
        "served via the static files endpoint at `/static/products/{id}/{filename}`.\n\n"
        "**Requires role:** Admin or Apoteker."
    ),
    responses={
        200: {"description": "Image saved and product.image_url updated"},
        400: {"description": "Unsupported file type or file too large"},
        404: {"description": "Product not found"},
    },
)
async def upload_product_image(
    product_id: int,
    request: Request,
    file: UploadFile = File(
        ...,
        description="Product image — JPEG, PNG, or WebP only. Max 2 MB.",
    ),
    current_user: User = Depends(RequireAdminOrApoteker),
    service: ProductService = Depends(_get_service),
) -> ImageUploadResponse:
    """
    Upload and save a product image.

    Validates MIME type, enforces max file size from settings,
    saves with a UUID filename to prevent collisions,
    deletes the previous image if one existed,
    and persists the relative path in products.image_url.
    """
    return await service.upload_product_image(product_id, file, current_user, request)
