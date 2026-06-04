"""
product_repository.py — Data Access Layer for products, categories, and suppliers.

All methods are async and operate within a caller-supplied AsyncSession.
Business logic lives in product_service.py — this layer is pure SQL.

Key query patterns:
  • list_products  — dynamic WHERE clause built from filter params + COUNT query
                     for accurate pagination totals without a separate COUNT(*) call
  • search         — ilike on (name, sku, description) for case-insensitive match
  • bulk_create    — batch INSERT via db.add_all() + flush, which PostgreSQL executes
                     as a single multi-row statement (much faster than N individual INSERTs)
  • update         — only sets columns that are explicitly provided (partial update)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Category, Product, Supplier
from app.schemas.product import ProductFilterParams, ProductSortField, SortOrder

logger = logging.getLogger(__name__)

# ── Sort field → ORM column mapping ──────────────────────────────────────────

_SORT_COLUMNS: dict[ProductSortField, object] = {
    ProductSortField.NAME: Product.name,
    ProductSortField.PRICE: Product.price,
    ProductSortField.SKU: Product.sku,
    ProductSortField.CREATED_AT: Product.created_at,
    ProductSortField.UPDATED_AT: Product.updated_at,
}


class ProductRepository:
    """
    Encapsulates all database queries for the products table.

    Instantiate with an AsyncSession:
        repo = ProductRepository(db)
        product = await repo.get_by_id(42)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Lookups ───────────────────────────────────────────────────────────────

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """Fetch a single product with category and supplier eagerly loaded."""
        result = await self.db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Fetch by SKU (case-insensitive — SKUs are stored uppercase)."""
        result = await self.db.execute(
            select(Product).where(Product.sku == sku.upper().strip())
        )
        return result.scalar_one_or_none()

    async def exists_by_sku(self, sku: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check SKU uniqueness.

        Pass `exclude_id` on updates to allow re-saving the same SKU on the
        same product without a false-positive conflict.
        """
        stmt = select(Product.id).where(Product.sku == sku.upper().strip())
        if exclude_id:
            stmt = stmt.where(Product.id != exclude_id)
        stmt = stmt.limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ── Paginated list ────────────────────────────────────────────────────────

    async def list_products(
        self,
        filters: ProductFilterParams,
        page: int,
        page_size: int,
    ) -> Tuple[list[Product], int]:
        """
        Return (items, total_count) for paginated product list.

        Runs two queries:
          1. COUNT query — returns total matching rows for pagination metadata.
          2. SELECT query — returns the page items with eager-loaded relations.

        Both queries share the same WHERE clause (built once, applied twice).
        """
        # ── Build shared WHERE predicates ─────────────────────────────────────
        conditions = []

        if filters.is_active is not None:
            conditions.append(Product.is_active == filters.is_active)

        if filters.q:
            search_term = f"%{filters.q.strip()}%"
            conditions.append(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.description.ilike(search_term),
                )
            )

        if filters.category_id is not None:
            conditions.append(Product.category_id == filters.category_id)

        if filters.supplier_id is not None:
            conditions.append(Product.supplier_id == filters.supplier_id)

        if filters.requires_prescription is not None:
            conditions.append(
                Product.requires_prescription == filters.requires_prescription
            )

        if filters.min_price is not None:
            conditions.append(Product.price >= filters.min_price)

        if filters.max_price is not None:
            conditions.append(Product.price <= filters.max_price)

        # ── COUNT query ───────────────────────────────────────────────────────
        count_stmt = select(func.count(Product.id)).where(*conditions)
        total: int = (await self.db.execute(count_stmt)).scalar_one()

        # ── Sort column ───────────────────────────────────────────────────────
        sort_col = _SORT_COLUMNS.get(filters.sort_by, Product.name)
        sort_expr = sort_col.asc() if filters.sort_order == SortOrder.ASC else sort_col.desc()  # type: ignore[union-attr]

        # ── Paginated SELECT ──────────────────────────────────────────────────
        offset = (page - 1) * page_size
        data_stmt = (
            select(Product)
            .where(*conditions)
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
            )
            .order_by(sort_expr)
            .offset(offset)
            .limit(page_size)
        )
        rows = (await self.db.execute(data_stmt)).scalars().all()
        return list(rows), total

    # ── Reference data lookups (for FK validation) ────────────────────────────

    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        result = await self.db.execute(
            select(Category).where(Category.id == category_id, Category.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_supplier_by_id(self, supplier_id: int) -> Optional[Supplier]:
        result = await self.db.execute(
            select(Supplier).where(Supplier.id == supplier_id, Supplier.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_all_active_category_ids(self) -> set[int]:
        """Pre-load all valid category IDs for batch import validation."""
        result = await self.db.execute(
            select(Category.id).where(Category.is_active == True)
        )
        return {row[0] for row in result.all()}

    async def get_all_active_supplier_ids(self) -> set[int]:
        """Pre-load all valid supplier IDs for batch import validation."""
        result = await self.db.execute(
            select(Supplier.id).where(Supplier.is_active == True)
        )
        return {row[0] for row in result.all()}

    async def get_all_existing_skus(self) -> set[str]:
        """Pre-load all existing SKUs for batch import duplicate detection."""
        result = await self.db.execute(select(Product.sku))
        return {row[0] for row in result.all()}

    # ── Writes ────────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        sku: str,
        name: str,
        category_id: int,
        supplier_id: int,
        price: Decimal,
        description: Optional[str] = None,
        composition: Optional[str] = None,
        dosage: Optional[str] = None,
        side_effects: Optional[str] = None,
        requires_prescription: bool = False,
        min_stock_threshold: int = 10,
        image_url: Optional[str] = None,
    ) -> Product:
        """Insert a new product row and flush to get DB-assigned id."""
        product = Product(
            sku=sku.upper().strip(),
            name=name.strip(),
            category_id=category_id,
            supplier_id=supplier_id,
            price=price,
            description=description,
            composition=composition,
            dosage=dosage,
            side_effects=side_effects,
            requires_prescription=requires_prescription,
            min_stock_threshold=min_stock_threshold,
            image_url=image_url,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product, attribute_names=["category", "supplier"])
        return product

    async def update(
        self,
        product: Product,
        updates: dict,
    ) -> Product:
        """
        Apply a dict of field → value updates to a Product instance.

        Only keys present in `updates` are applied — None values explicitly
        passed mean "set this field to NULL".
        """
        for field, value in updates.items():
            if hasattr(product, field):
                setattr(product, field, value)
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product, attribute_names=["category", "supplier"])
        return product

    async def soft_delete(self, product: Product) -> Product:
        """Mark product as inactive (soft-delete). Data is preserved."""
        product.is_active = False
        self.db.add(product)
        await self.db.flush()
        return product

    async def update_image_url(self, product: Product, image_url: str) -> Product:
        """Persist the uploaded image path to the product row."""
        product.image_url = image_url
        self.db.add(product)
        await self.db.flush()
        return product

    async def bulk_create(self, products: list[Product]) -> list[Product]:
        """
        Batch-insert multiple Product ORM objects.

        Uses db.add_all() which SQLAlchemy translates into an efficient
        multi-row INSERT on flush, far faster than N individual inserts.
        """
        self.db.add_all(products)
        await self.db.flush()
        logger.info("Bulk inserted %d products", len(products))
        return products
