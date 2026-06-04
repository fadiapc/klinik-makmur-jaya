"""
product_service.py — Business logic for the Products management module.

Covers PRD sections 4.3 (CRUD-01 through CRUD-05) and 4.5 (PAR-01, PAR-02).

Parallel / background processing
─────────────────────────────────
The batch CSV import (PAR-02) is implemented with FastAPI BackgroundTasks:

  1. Route handler reads the uploaded file bytes in-request.
  2. Route handler registers an ImportJob and returns a job_id immediately
     (HTTP 202 Accepted — the response is sent WITHOUT waiting for processing).
  3. BackgroundTask runs `_execute_csv_import()` after the response:
       • Creates its own AsyncSession (the request session is already closed).
       • Parses CSV with pandas in-memory (no temp file needed).
       • Pre-fetches all valid category/supplier IDs in two queries.
       • Processes rows, collecting per-row errors.
       • Bulk-inserts valid rows with db.add_all() — single round-trip.
       • Writes a BATCH_IMPORT_PRODUCT audit log.
       • Updates the ImportJob status so polling clients see the result.

  ImportJobStore is an in-memory singleton. In production, replace with
  Redis (e.g. `await redis.set(job_id, json.dumps(job_data), ex=3600)`).

Image upload
────────────
  • Validates MIME type (image/jpeg, image/png, image/webp).
  • Validates file size (≤ settings.MAX_UPLOAD_SIZE_MB).
  • Saves to {UPLOAD_DIR}/products/{product_id}/{uuid4}{ext}.
  • Stores the relative path in products.image_url.
  • Served to clients via FastAPI StaticFiles at /static/<path>.
"""

from __future__ import annotations

import asyncio
import io
import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import Category, Product, Supplier, User
from app.repositories.product_repository import ProductRepository
from app.schemas.common import PaginatedResponse
from app.schemas.product import (
    BatchImportResponse,
    ImportJobStatusEnum,
    ImportJobStatusResponse,
    ImportRowError,
    ProductCreate,
    ProductFilterParams,
    ProductOut,
    ProductUpdate,
    ImageUploadResponse,
)
from app.utils.audit import log_audit

logger = logging.getLogger(__name__)

# ── Allowed image MIME types (PRD DASH-04) ────────────────────────────────────
_ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
_ALLOWED_IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}

# ── CSV required columns ──────────────────────────────────────────────────────
_REQUIRED_CSV_COLS: set[str] = {"sku", "name", "category_id", "supplier_id", "price"}
_OPTIONAL_CSV_COLS: set[str] = {
    "description", "composition", "dosage", "side_effects",
    "requires_prescription", "min_stock_threshold", "image_url",
}
_ALL_KNOWN_COLS: set[str] = _REQUIRED_CSV_COLS | _OPTIONAL_CSV_COLS


# ══════════════════════════════════════════════════════════════════════════════
# § 1  In-memory Import Job Store
#      Replace with Redis in production for multi-process / multi-server deployments.
# ══════════════════════════════════════════════════════════════════════════════


class _ImportJobStore:
    """
    Thread-safe (asyncio Lock) in-memory store for import job metadata.

    In production: replace body of each method with Redis GET/SET calls.
    Jobs expire from memory after `_MAX_JOBS` entries (FIFO eviction).
    """

    _MAX_JOBS = 500  # prevent unbounded memory growth in long-running processes

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def create(self, job_id: str, filename: str) -> dict:
        async with self._lock:
            job: dict = {
                "job_id": job_id,
                "filename": filename,
                "status": ImportJobStatusEnum.PENDING,
                "total_rows": 0,
                "successful": 0,
                "failed": 0,
                "errors": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "fatal_error": None,
            }
            # Evict oldest entry if at capacity
            if len(self._jobs) >= self._MAX_JOBS:
                oldest_key = next(iter(self._jobs))
                del self._jobs[oldest_key]
            self._jobs[job_id] = job
            return dict(job)

    async def get(self, job_id: str) -> Optional[dict]:
        return self._jobs.get(job_id)

    async def patch(self, job_id: str, **kwargs) -> None:
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)


# Module-level singleton — shared across all requests in the same process
import_job_store = _ImportJobStore()


# ══════════════════════════════════════════════════════════════════════════════
# § 2  CSV parsing helpers (runs inside background task)
# ══════════════════════════════════════════════════════════════════════════════


def _parse_bool_from_csv(val) -> bool:
    """Tolerantly parse truthy values from CSV cells."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "y")
    return False


def _parse_decimal(val) -> Optional[Decimal]:
    """Convert CSV cell to Decimal; return None on failure."""
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, ValueError):
        return None


def _parse_int(val) -> Optional[int]:
    """Convert CSV cell to int; return None on failure."""
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


# ══════════════════════════════════════════════════════════════════════════════
# § 3  Background task — CSV import execution
# ══════════════════════════════════════════════════════════════════════════════


async def _execute_csv_import(
    job_id: str,
    csv_bytes: bytes,
    triggered_by_user_id: int,
) -> None:
    """
    Background coroutine: parse CSV bytes and bulk-insert valid products.

    This function runs AFTER the HTTP response is sent, in the same asyncio
    event loop.  It creates its own DB session (the request session is gone).

    Error strategy:
      • Per-row errors are collected and attached to the job — they do not
        abort the whole import.
      • A fatal error (e.g. malformed CSV, no valid rows) aborts immediately
        and marks the job FAILED.
      • The DB transaction is committed only once at the end — either all
        valid rows land or none do (ACID).
    """
    import pandas as pd  # local import — not needed at module load time

    await import_job_store.patch(
        job_id, status=ImportJobStatusEnum.PROCESSING
    )
    logger.info("CSV import job %s started", job_id)

    async with AsyncSessionLocal() as db:
        try:
            # ── Parse CSV ─────────────────────────────────────────────────────
            try:
                df = pd.read_csv(io.BytesIO(csv_bytes), dtype=str, keep_default_na=False)
            except Exception as exc:
                raise ValueError(f"Cannot parse CSV file: {exc}") from exc

            # Normalise column names (strip whitespace, lowercase)
            df.columns = [c.strip().lower() for c in df.columns]

            # Validate required columns
            missing_cols = _REQUIRED_CSV_COLS - set(df.columns)
            if missing_cols:
                raise ValueError(
                    f"CSV is missing required columns: {sorted(missing_cols)}. "
                    f"Required: {sorted(_REQUIRED_CSV_COLS)}"
                )

            total_rows = len(df)
            await import_job_store.patch(job_id, total_rows=total_rows)

            if total_rows == 0:
                raise ValueError("CSV file contains no data rows.")

            # ── Pre-load reference data (2 queries vs N per-row lookups) ──────
            valid_category_ids: set[int] = set(
                r[0] for r in (await db.execute(
                    select(Category.id).where(Category.is_active == True)
                )).all()
            )
            valid_supplier_ids: set[int] = set(
                r[0] for r in (await db.execute(
                    select(Supplier.id).where(Supplier.is_active == True)
                )).all()
            )
            existing_skus: set[str] = set(
                r[0] for r in (await db.execute(select(Product.sku))).all()
            )
            # Track SKUs seen in THIS CSV (prevents duplicate SKUs within the file)
            seen_in_batch: set[str] = set()

            # ── Process rows ──────────────────────────────────────────────────
            products_to_insert: list[Product] = []
            row_errors: list[dict] = []

            for idx, row in df.iterrows():
                row_num = int(idx) + 2  # 1-based, +1 for header, +1 for 0-index
                raw_sku = str(row.get("sku", "")).strip().upper()
                row_errors_this: list[str] = []

                # Required: sku
                if not raw_sku:
                    row_errors_this.append("'sku' is empty")
                elif raw_sku in existing_skus:
                    row_errors_this.append(f"SKU '{raw_sku}' already exists in the database")
                elif raw_sku in seen_in_batch:
                    row_errors_this.append(f"SKU '{raw_sku}' is duplicated within this CSV")

                # Required: name
                raw_name = str(row.get("name", "")).strip()
                if not raw_name:
                    row_errors_this.append("'name' is empty")

                # Required: category_id
                cat_id = _parse_int(row.get("category_id", ""))
                if cat_id is None:
                    row_errors_this.append("'category_id' is not a valid integer")
                elif cat_id not in valid_category_ids:
                    row_errors_this.append(
                        f"category_id={cat_id} does not exist or is inactive"
                    )

                # Required: supplier_id
                sup_id = _parse_int(row.get("supplier_id", ""))
                if sup_id is None:
                    row_errors_this.append("'supplier_id' is not a valid integer")
                elif sup_id not in valid_supplier_ids:
                    row_errors_this.append(
                        f"supplier_id={sup_id} does not exist or is inactive"
                    )

                # Required: price
                price = _parse_decimal(row.get("price", ""))
                if price is None:
                    row_errors_this.append("'price' is not a valid number")
                elif price <= 0:
                    row_errors_this.append("'price' must be greater than 0")

                # If any required field failed — skip this row
                if row_errors_this:
                    row_errors.append({
                        "row": row_num,
                        "sku": raw_sku or None,
                        "error": "; ".join(row_errors_this),
                    })
                    continue

                # Optional fields
                requires_rx = _parse_bool_from_csv(row.get("requires_prescription", "false"))
                min_threshold = _parse_int(row.get("min_stock_threshold", "10")) or 10

                product = Product(
                    sku=raw_sku,
                    name=raw_name,
                    category_id=cat_id,        # type: ignore[arg-type]
                    supplier_id=sup_id,         # type: ignore[arg-type]
                    price=price,
                    description=str(row.get("description", "")).strip() or None,
                    composition=str(row.get("composition", "")).strip() or None,
                    dosage=str(row.get("dosage", "")).strip() or None,
                    side_effects=str(row.get("side_effects", "")).strip() or None,
                    requires_prescription=requires_rx,
                    min_stock_threshold=min_threshold,
                    image_url=str(row.get("image_url", "")).strip() or None,
                )
                products_to_insert.append(product)
                seen_in_batch.add(raw_sku)
                existing_skus.add(raw_sku)  # prevent cross-chunk duplicates if batched later

            # ── Bulk insert valid rows ─────────────────────────────────────────
            successful = len(products_to_insert)
            if products_to_insert:
                db.add_all(products_to_insert)
                await db.flush()

                # Audit log (single entry for the batch)
                await log_audit(
                    db=db,
                    user_id=triggered_by_user_id,
                    action="BATCH_IMPORT_PRODUCT",
                    module="PRODUCT",
                    new_value={
                        "job_id": job_id,
                        "total_rows": total_rows,
                        "successful": successful,
                        "failed": len(row_errors),
                    },
                )
                await db.commit()
                logger.info(
                    "CSV import job %s committed %d products (%d errors)",
                    job_id, successful, len(row_errors),
                )
            else:
                logger.warning("CSV import job %s: no valid rows to insert", job_id)

            # ── Update job status ─────────────────────────────────────────────
            await import_job_store.patch(
                job_id,
                status=ImportJobStatusEnum.COMPLETED,
                successful=successful,
                failed=len(row_errors),
                errors=row_errors,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        except ValueError as exc:
            # Fatal structural error — entire job fails
            await db.rollback()
            logger.error("CSV import job %s FAILED: %s", job_id, exc)
            await import_job_store.patch(
                job_id,
                status=ImportJobStatusEnum.FAILED,
                fatal_error=str(exc),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            await db.rollback()
            logger.exception("CSV import job %s unexpected failure", job_id)
            await import_job_store.patch(
                job_id,
                status=ImportJobStatusEnum.FAILED,
                fatal_error=f"Internal error: {type(exc).__name__}: {exc}",
                completed_at=datetime.now(timezone.utc).isoformat(),
            )


# ══════════════════════════════════════════════════════════════════════════════
# § 4  ProductService
# ══════════════════════════════════════════════════════════════════════════════


class ProductService:
    """
    Business logic for the products module.

    Instantiate with a live AsyncSession:
        svc = ProductService(db)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    # ── CRUD — Create ─────────────────────────────────────────────────────────

    async def create_product(
        self,
        data: ProductCreate,
        current_user: User,
        request: Request,
    ) -> ProductOut:
        """
        Create a new product.

        Raises:
            HTTP 409 — SKU already taken
            HTTP 404 — category or supplier not found / inactive
        """
        # SKU uniqueness
        if await self.repo.exists_by_sku(data.sku):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A product with SKU '{data.sku.upper()}' already exists.",
            )

        # FK validation — category
        if not await self.repo.get_category_by_id(data.category_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id={data.category_id} not found or inactive.",
            )

        # FK validation — supplier
        if not await self.repo.get_supplier_by_id(data.supplier_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id={data.supplier_id} not found or inactive.",
            )

        product = await self.repo.create(
            sku=data.sku,
            name=data.name,
            category_id=data.category_id,
            supplier_id=data.supplier_id,
            price=data.price,
            description=data.description,
            composition=data.composition,
            dosage=data.dosage,
            side_effects=data.side_effects,
            requires_prescription=data.requires_prescription,
            min_stock_threshold=data.min_stock_threshold,
        )

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="CREATE_PRODUCT",
            module="PRODUCT",
            target_type="Product",
            target_id=product.id,
            new_value={"sku": product.sku, "name": product.name, "price": str(product.price)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        logger.info("Product created | id=%d sku=%s by user_id=%d", product.id, product.sku, current_user.id)
        return ProductOut.from_orm_model(product)

    # ── CRUD — Read single ────────────────────────────────────────────────────

    async def get_product(self, product_id: int) -> ProductOut:
        """
        Fetch a single product by id.

        Raises:
            HTTP 404 — product not found
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id={product_id} not found.",
            )
        return ProductOut.from_orm_model(product)

    # ── CRUD — Read list (paginated + filtered) ───────────────────────────────

    async def list_products(
        self,
        filters: ProductFilterParams,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[ProductOut]:
        """
        Return a paginated, filtered, sorted product list.
        """
        products, total = await self.repo.list_products(filters, page, page_size)
        items = [ProductOut.from_orm_model(p) for p in products]
        return PaginatedResponse.build(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── CRUD — Update ─────────────────────────────────────────────────────────

    async def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
        current_user: User,
        request: Request,
    ) -> ProductOut:
        """
        Partially update a product.

        Only fields explicitly provided in the request body are applied.

        Raises:
            HTTP 404 — product not found
            HTTP 409 — new SKU conflicts with existing product
            HTTP 404 — new category or supplier not found
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id={product_id} not found.",
            )

        # Build update dict — only include non-None fields
        update_dict: dict = {
            k: v for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None or data.model_fields_set.__contains__(k)
        }

        # Validate new category FK if provided
        if "category_id" in update_dict:
            if not await self.repo.get_category_by_id(update_dict["category_id"]):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id={update_dict['category_id']} not found.",
                )

        # Validate new supplier FK if provided
        if "supplier_id" in update_dict:
            if not await self.repo.get_supplier_by_id(update_dict["supplier_id"]):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Supplier with id={update_dict['supplier_id']} not found.",
                )

        # Capture old state for audit log
        old_snapshot = {
            "sku": product.sku,
            "name": product.name,
            "price": str(product.price),
            "is_active": product.is_active,
        }

        updated_product = await self.repo.update(product, update_dict)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="UPDATE_PRODUCT",
            module="PRODUCT",
            target_type="Product",
            target_id=product_id,
            old_value=old_snapshot,
            new_value={k: str(v) if isinstance(v, Decimal) else v for k, v in update_dict.items()},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return ProductOut.from_orm_model(updated_product)

    # ── CRUD — Soft delete ────────────────────────────────────────────────────

    async def delete_product(
        self,
        product_id: int,
        current_user: User,
        request: Request,
    ) -> None:
        """
        Soft-delete a product (sets is_active=False).

        Raises:
            HTTP 404 — product not found
            HTTP 409 — product already inactive
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id={product_id} not found.",
            )
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product is already inactive.",
            )

        await self.repo.soft_delete(product)
        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="DELETE_PRODUCT",
            module="PRODUCT",
            target_type="Product",
            target_id=product_id,
            old_value={"sku": product.sku, "name": product.name, "is_active": True},
            new_value={"is_active": False},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        logger.info("Product soft-deleted | id=%d sku=%s by user_id=%d", product_id, product.sku, current_user.id)

    # ── Batch CSV import ──────────────────────────────────────────────────────

    async def start_batch_import(
        self,
        file: UploadFile,
        current_user: User,
    ) -> BatchImportResponse:
        """
        Validate the uploaded file, register an import job, and enqueue
        the background task.

        Returns immediately (HTTP 202) — the caller adds the background task
        after calling this method.

        Raises:
            HTTP 400 — wrong MIME type (not CSV) or file too large
        """
        # Validate MIME type
        if file.content_type not in ("text/csv", "application/csv", "text/plain"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid file type '{file.content_type}'. "
                    "Please upload a CSV file (text/csv)."
                ),
            )

        # Validate file size — read all bytes here (before task starts)
        csv_bytes = await file.read()
        max_bytes = 10 * 1024 * 1024  # 10 MB limit for CSV files
        if len(csv_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV file too large ({len(csv_bytes) // 1024} KB). Maximum is 10 MB.",
            )

        if len(csv_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded CSV file is empty.",
            )

        # Create import job record
        job_id = str(uuid.uuid4())
        await import_job_store.create(job_id, file.filename or "import.csv")

        logger.info(
            "Batch import job %s registered | file=%s user_id=%d",
            job_id,
            file.filename,
            current_user.id,
        )

        # Return bytes AND job_id so the route handler can pass them to background task
        # We store bytes on the store so the background function can pick it up
        # (Alternative: pass bytes directly via BackgroundTasks closure)
        self._pending_csv_bytes = csv_bytes
        self._pending_job_id = job_id
        self._pending_user_id = current_user.id

        return BatchImportResponse(
            job_id=job_id,
            filename=file.filename or "import.csv",
        )

    def get_pending_import_params(self) -> tuple[str, bytes, int]:
        """Retrieve parameters stored during start_batch_import for use by BackgroundTask."""
        return self._pending_job_id, self._pending_csv_bytes, self._pending_user_id

    # ── Image upload ──────────────────────────────────────────────────────────

    async def upload_product_image(
        self,
        product_id: int,
        file: UploadFile,
        current_user: User,
        request: Request,
    ) -> ImageUploadResponse:
        """
        Validate and save a product image; update products.image_url.

        Storage path: {UPLOAD_DIR}/products/{product_id}/{uuid4}{ext}
        Served at:    /static/products/{product_id}/{uuid4}{ext}

        Raises:
            HTTP 404 — product not found
            HTTP 400 — unsupported MIME type or file too large
        """
        # Product existence check
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id={product_id} not found.",
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

        # Read bytes for size validation
        image_bytes = await file.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(image_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Image file too large ({len(image_bytes) / 1024:.1f} KB). "
                    f"Maximum is {settings.MAX_UPLOAD_SIZE_MB} MB."
                ),
            )

        # Determine file extension
        ext = Path(file.filename or "").suffix.lower()
        if not ext or ext not in _ALLOWED_IMAGE_EXTENSIONS:
            # Fall back to MIME-derived extension
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            ext = ".jpg" if ext == ".jpe" else ext  # normalise .jpe → .jpg

        # Build storage path
        upload_root = Path(settings.UPLOAD_DIR)
        product_dir = upload_root / "products" / str(product_id)
        product_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}{ext}"
        file_path = product_dir / filename

        # Write bytes to disk
        file_path.write_bytes(image_bytes)
        logger.info("Image saved to %s (%d bytes)", file_path, len(image_bytes))

        # Relative URL stored in DB and returned to client
        relative_url = f"products/{product_id}/{filename}"

        # Delete old image file if it exists and is local
        if product.image_url:
            old_path = upload_root / product.image_url
            if old_path.exists() and old_path.is_file():
                try:
                    old_path.unlink()
                    logger.debug("Deleted old image: %s", old_path)
                except OSError as exc:
                    logger.warning("Could not delete old image %s: %s", old_path, exc)

        # Persist new URL in DB
        await self.repo.update_image_url(product, relative_url)

        await log_audit(
            db=self.db,
            user_id=current_user.id,
            action="UPLOAD_PRODUCT_IMAGE",
            module="PRODUCT",
            target_type="Product",
            target_id=product_id,
            old_value={"image_url": product.image_url},
            new_value={"image_url": relative_url},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return ImageUploadResponse(
            product_id=product_id,
            image_url=relative_url,
        )

    # ── Import status ─────────────────────────────────────────────────────────

    @staticmethod
    async def get_import_job_status(job_id: str) -> ImportJobStatusResponse:
        """
        Retrieve the current state of a batch import job.

        Raises:
            HTTP 404 — job_id not found (expired or never created)
        """
        job = await import_job_store.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Import job '{job_id}' not found. "
                    "Jobs expire from memory after the process restarts. "
                    "Use Redis in production for persistence."
                ),
            )
        errors = [ImportRowError(**e) for e in job.get("errors", [])]
        return ImportJobStatusResponse(
            job_id=job["job_id"],
            filename=job["filename"],
            status=job["status"],
            total_rows=job["total_rows"],
            successful=job["successful"],
            failed=job["failed"],
            errors=errors,
            created_at=job["created_at"],
            completed_at=job.get("completed_at"),
            fatal_error=job.get("fatal_error"),
        )
