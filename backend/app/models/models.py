"""
models.py — Complete SQLAlchemy ORM models for Klinik Makmur Jaya.

Implements every table defined in PRD Section 7.2:
  users, roles, products, categories, suppliers, stock_batches,
  orders, order_items, prescriptions, audit_logs

Key design decisions
────────────────────
• All primary keys use BigInteger IDENTITY (PostgreSQL GENERATED ALWAYS AS IDENTITY).
• UUID columns use server-side gen_random_uuid() to avoid leaking sequential IDs in
  public-facing APIs.
• ENUM types are implemented as Python enums + PostgreSQL native ENUM types
  (SQLAlchemy `Enum(MyEnum)` handles DDL creation and type-checking simultaneously).
• orders ↔ prescriptions is a strict 1:1 enforced by:
    - UNIQUE constraint on prescriptions.order_id (DB-level uniqueness)
    - `uselist=False` on the SQLAlchemy relationship (ORM-level)
    - `back_populates` on both sides for bidirectional navigation
• All monetary columns use Numeric(12, 2) — never Float — to avoid IEEE-754
  rounding issues in financial calculations.
• Soft-delete is implemented via `is_active` BOOLEAN columns (no physical deletion).
• JSON columns (audit_logs.old_value / new_value) use PostgreSQL native JSONB for
  indexability and better storage efficiency.
• Indexes defined here mirror Section 7.3 of the PRD including composite and
  full-text search indexes.
• Timestamps are always stored in UTC (see database.py TimeZone=UTC setting).
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ══════════════════════════════════════════════════════════════════════════════
# § 1  Enumeration types
#       Declared as Python enums so application code can use them by name,
#       and SQLAlchemy generates matching PostgreSQL ENUM types in migrations.
# ══════════════════════════════════════════════════════════════════════════════


class OrderStatus(str, enum.Enum):
    """
    Lifecycle states of an order — 7 status sesuai spesifikasi operasional klinik.

    Alur Normal:
      MENUNGGU_VERIFIKASI_RESEP → MENUNGGU_PEMBAYARAN → MENUNGGU_KONFIRMASI_KASIR
      → DIPROSES → DIKIRIM → SELESAI

    Alur Gagal (terminal):
      DIBATALKAN
    """

    MENUNGGU_VERIFIKASI_RESEP = "menunggu_verifikasi_resep"
    MENUNGGU_PEMBAYARAN = "menunggu_pembayaran"
    MENUNGGU_KONFIRMASI_KASIR = "menunggu_konfirmasi_kasir"
    DIPROSES = "diproses"
    DIKIRIM = "dikirim"
    SELESAI = "selesai"
    DIBATALKAN = "dibatalkan"


class OrderType(str, enum.Enum):
    """Channel through which the order was placed."""

    ONLINE = "online"
    COUNTER = "counter"


class PaymentMethod(str, enum.Enum):
    """Accepted payment instruments."""

    CASH = "cash"
    TRANSFER = "transfer"
    QRIS = "qris"


class PaymentStatus(str, enum.Enum):
    """Settlement state of the payment."""

    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


class PrescriptionStatus(str, enum.Enum):
    """Pharmacist review outcome for an uploaded prescription."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ══════════════════════════════════════════════════════════════════════════════
# § 2  Lookup / reference tables
#       roles, categories, suppliers — small, rarely-mutated master data.
# ══════════════════════════════════════════════════════════════════════════════


class Role(Base):
    """
    roles — User role master table.

    PRD roles: Admin, Apoteker (Pharmacist), Kasir (Cashier), Pasien (Patient).
    Stored in the DB rather than hard-coded so new roles can be added without
    a code deploy.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Role primary key (auto-increment integer — small table)",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Role name, e.g. 'admin', 'apoteker', 'kasir', 'pasien'",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Human-readable description of the role's permissions",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp (UTC)",
    )

    # Relationships
    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="role",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"


class Category(Base):
    """
    categories — Drug category master table.

    PRD categories: resep (prescription), bebas (OTC), suplemen, alkes (medical devices).
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Category primary key",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Category name (e.g. 'Obat Resep', 'Obat Bebas')",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Category description",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Soft-delete flag; False hides category from UI",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"


class Supplier(Base):
    """
    suppliers — Drug distributor / supplier master table.

    One supplier can supply many products (1:M with products).
    """

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Supplier primary key",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Supplier / distributor company name",
    )
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Name of the primary contact at the supplier",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Supplier contact phone number",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Supplier contact email address",
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Supplier physical address",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Soft-delete flag",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="supplier",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name={self.name!r}>"


# ══════════════════════════════════════════════════════════════════════════════
# § 3  users
# ══════════════════════════════════════════════════════════════════════════════


class User(Base):
    """
    users — Platform accounts for all roles (Admin, Apoteker, Kasir, Pasien).

    Security notes:
    • `password_hash` stores the Bcrypt/Argon2 digest — NEVER the plaintext.
    • `uuid` is the only identifier exposed in public API responses; the
      internal `id` (BigInteger) is used exclusively for FK joins.
    • `is_active` enables soft-disable without losing audit history.
    """

    __tablename__ = "users"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Internal BigInteger PK — never expose in public APIs",
    )

    # ── Public identifier ────────────────────────────────────────────────────
    uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        server_default=func.gen_random_uuid().cast(String),
        comment="RFC-4122 UUID for public-facing references (hides sequential IDs)",
    )

    # ── Core fields ──────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Full name of the user",
    )
    email: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
        comment="Login email — must be globally unique",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt or Argon2 hash of the user password",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Contact phone number (optional)",
    )

    # ── Role FK ──────────────────────────────────────────────────────────────
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → roles.id (M:1 — every user has exactly one role)",
    )

    # ── Status flags ─────────────────────────────────────────────────────────
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True after OTP email verification is completed",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Soft-disable: set False to lock account without deletion",
    )

    # ── Audit timestamps ─────────────────────────────────────────────────────
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the most recent successful login",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Account creation timestamp (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last profile update timestamp (UTC)",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    role: Mapped[Role] = relationship(
        "Role",
        back_populates="users",
        lazy="joined",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        foreign_keys="[Order.user_id]",
        back_populates="customer",
        lazy="selectin",
    )
    cashier_orders: Mapped[list[Order]] = relationship(
        "Order",
        foreign_keys="[Order.cashier_id]",
        back_populates="cashier",
        lazy="selectin",
    )
    # Prescriptions this user uploaded (as patient)
    prescriptions_as_patient: Mapped[list[Prescription]] = relationship(
        "Prescription",
        foreign_keys="[Prescription.patient_id]",
        back_populates="patient",
        lazy="selectin",
    )
    # Prescriptions this user reviewed (as pharmacist)
    prescriptions_as_pharmacist: Mapped[list[Prescription]] = relationship(
        "Prescription",
        foreign_keys="[Prescription.pharmacist_id]",
        back_populates="pharmacist",
        lazy="selectin",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role_id={self.role_id}>"


# ══════════════════════════════════════════════════════════════════════════════
# § 4  products
# ══════════════════════════════════════════════════════════════════════════════


class Product(Base):
    """
    products — Drug / medical product catalogue (2 000+ SKUs).

    • `requires_prescription` drives cart validation — pharmacist approval
      is required before checkout if True.
    • `min_stock_threshold` triggers the NOTIF-01 stock-alert when
      total stock (sum of active stock_batches) falls below this value.
    • `is_active` = False hides the product from the catalogue (soft-delete).
    • Full-text search index on (name, description) as per PRD § 7.3.
    """

    __tablename__ = "products"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Product internal PK",
    )

    # ── Catalogue identifiers ─────────────────────────────────────────────────
    sku: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Stock Keeping Unit — globally unique product code",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Drug/product name (indexed for text search)",
    )

    # ── Category & Supplier FKs ───────────────────────────────────────────────
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → categories.id (M:1 — product belongs to one category)",
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → suppliers.id (M:1 — product sourced from one supplier)",
    )

    # ── Pharmaceutical details ────────────────────────────────────────────────
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="General drug description",
    )
    composition: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Active ingredient composition",
    )
    dosage: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Dosage instructions",
    )
    side_effects: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Known side effects",
    )

    # ── Pricing & stock policy ────────────────────────────────────────────────
    price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Retail selling price per unit (IDR)",
    )
    requires_prescription: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True = obat keras; purchase requires pharmacist-approved prescription",
    )
    min_stock_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="10",
        comment="Minimum stock before NOTIF-01 low-stock alert fires",
    )

    # ── Media ─────────────────────────────────────────────────────────────────
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Relative or absolute path to the product image",
    )

    # ── Soft-delete ───────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Soft-delete flag; False removes product from catalogue API",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    category: Mapped[Category] = relationship(
        "Category",
        back_populates="products",
        lazy="joined",
    )
    supplier: Mapped[Supplier] = relationship(
        "Supplier",
        back_populates="products",
        lazy="joined",
    )
    stock_batches: Mapped[list[StockBatch]] = relationship(
        "StockBatch",
        back_populates="product",
        order_by="StockBatch.received_at",  # natural FIFO ordering
        lazy="selectin",
    )
    order_items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="product",
        lazy="selectin",
    )

    # ── Table-level constraints & indexes ─────────────────────────────────────
    __table_args__ = (
        # PRD § 7.3 — Full-text index on name + description for fuzzy search
        Index(
            "ix_products_fulltext",
            "name",
            "description",
            postgresql_using="gin",
            postgresql_ops={
                "name": "gin_trgm_ops",
                "description": "gin_trgm_ops",
            },
        ),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku!r} name={self.name!r}>"


# ══════════════════════════════════════════════════════════════════════════════
# § 5  stock_batches
# ══════════════════════════════════════════════════════════════════════════════


class StockBatch(Base):
    """
    stock_batches — Inventory batches per product (FIFO model).

    Each batch represents a distinct purchase/delivery from a supplier.
    FIFO stock deduction is implemented by ordering batches on `received_at`
    ascending and exhausting older batches first.

    PRD § 7.3 composite index: (product_id, expiry_date) supports both
    FIFO queries and the NOTIF-02 expiry-alert job.
    """

    __tablename__ = "stock_batches"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Batch PK",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → products.id (M:1 — batch belongs to one product)",
    )
    batch_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Manufacturer batch/lot number",
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Current available units in this batch",
    )
    purchase_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Cost price per unit for this batch (IDR)",
    )
    expiry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Batch expiry date — used for NOTIF-02 alerts and FIFO deduction",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when batch was received — primary FIFO sort key",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="stock_batches",
        lazy="joined",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # PRD § 7.3 — composite index for FIFO queries and expiry alerts
        Index("ix_stock_batches_product_expiry", "product_id", "expiry_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<StockBatch id={self.id} product_id={self.product_id} "
            f"batch={self.batch_number!r} qty={self.quantity}>"
        )


# ══════════════════════════════════════════════════════════════════════════════
# § 6  orders  +  order_items
# ══════════════════════════════════════════════════════════════════════════════


class Order(Base):
    """
    orders — Purchase transactions (both online and counter/POS).

    Financial columns use Numeric(12, 2) — never Float — to ensure exact
    arithmetic for IDR currency amounts.

    Relationships:
    • customer  (M:1 → users)       — always set
    • cashier   (M:1 → users)       — set only for COUNTER orders; NULL for ONLINE
    • items     (1:M → order_items) — the line items
    • prescription (1:1 → prescriptions, uselist=False) — strictly one prescription
      per order if required; enforced at DB level via UNIQUE on order_id FK.

    PRD § 7.3 indexes:
    • ix_orders_status         — single-column on status
    • ix_orders_created_at     — single-column on created_at
    • ix_orders_user_created   — composite (user_id, created_at) for history queries
    """

    __tablename__ = "orders"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Order internal PK",
    )

    # ── Human-readable code ───────────────────────────────────────────────────
    order_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Formatted order code e.g. ORD-20250601-001 — shown to customers",
    )

    # ── FK columns ────────────────────────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → users.id — the customer who placed this order",
    )
    cashier_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → users.id (Kasir role) — NULL for online orders",
    )

    # ── Status enums ──────────────────────────────────────────────────────────
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum", create_type=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=OrderStatus.MENUNGGU_PEMBAYARAN.value,
        index=True,
        comment="Current lifecycle status of the order (7-status lifecycle)",
    )
    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="order_type_enum", create_type=True),
        nullable=False,
        comment="Channel: 'online' (web) or 'counter' (POS/kasir)",
    )

    # ── Financial breakdown ───────────────────────────────────────────────────
    subtotal: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Sum of (unit_price × quantity) for all items before discounts/tax",
    )
    discount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default="0.00",
        comment="Total discount amount applied (IDR)",
    )
    tax: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default="0.00",
        comment="PPN 11% tax amount (IDR)",
    )
    grand_total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Final payable amount: subtotal - discount + tax (IDR)",
    )

    # ── Payment ───────────────────────────────────────────────────────────────
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum", create_type=True),
        nullable=False,
        comment="Selected payment instrument",
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum", create_type=True),
        nullable=False,
        server_default=PaymentStatus.UNPAID.value,
        comment="Settlement state of the payment",
    )

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text order notes from the customer or cashier",
    )

    # ── Payment proof (upload by customer) ───────────────────────────────────
    payment_proof_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Relative path to customer-uploaded payment proof image",
    )

    # ── Tracking / shipping number ────────────────────────────────────────────
    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Courier tracking number entered by Apoteker when shipping",
    )

    # ── Payment deadline (for auto-cancel background job) ─────────────────────
    payment_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC deadline for payment — order auto-cancelled if exceeded (1x24h)",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Order placement timestamp (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    customer: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="orders",
        lazy="joined",
    )
    cashier: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[cashier_id],
        back_populates="cashier_orders",
        lazy="joined",
    )
    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # ── 1:1 with Prescription — uselist=False is the critical ORM constraint ──
    prescription: Mapped[Optional[Prescription]] = relationship(
        "Prescription",
        back_populates="order",
        uselist=False,          # ← enforces 1:1 at ORM level
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ── Composite index: PRD § 7.3 ────────────────────────────────────────────
    __table_args__ = (
        Index("ix_orders_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Order id={self.id} code={self.order_code!r} "
            f"status={self.status.value} total={self.grand_total}>"
        )


class OrderItem(Base):
    """
    order_items — Individual line items within an order.

    `unit_price` is snapshotted at purchase time so historical order totals
    remain accurate even if the product price changes later.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Line-item PK",
    )
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → orders.id (M:1 — item belongs to one order)",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK → products.id (M:1 — item references one product)",
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of units purchased for this line item",
    )
    unit_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Product price at the moment of purchase (IDR) — immutable snapshot",
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="unit_price × quantity (IDR) — denormalised for query performance",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="items",
        lazy="joined",
    )
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="order_items",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItem id={self.id} order_id={self.order_id} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )


# ══════════════════════════════════════════════════════════════════════════════
# § 7  prescriptions
# ══════════════════════════════════════════════════════════════════════════════


class Prescription(Base):
    """
    prescriptions — Digital prescription attached to an order.

    STRICT 1:1 with orders:
    ─────────────────────────────────────────────────────────────────────────
    DB level  : UNIQUE constraint on `order_id` (defined in __table_args__)
                → PostgreSQL will reject any attempt to insert a second
                  prescription row for the same order.
    ORM level : `uselist=False` on `Order.prescription` relationship
                → SQLAlchemy returns a single object (or None), not a list.
    Both sides: `back_populates` links `Order.prescription` ↔
                `Prescription.order` for bidirectional navigation.
    ─────────────────────────────────────────────────────────────────────────

    Pharmacist workflow:
    1. Patient uploads a photo → status = PENDING
    2. Pharmacist reviews and calls approve/reject endpoint
       → status = APPROVED or REJECTED + rejection_reason filled
       → verified_at timestamp is set
    """

    __tablename__ = "prescriptions"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Prescription PK",
    )

    # ── Order FK (UNIQUE = 1:1 enforcement at DB level) ───────────────────────
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,            # ← THIS is what enforces 1:1 at the DB level
        comment=(
            "FK → orders.id. UNIQUE constraint ensures at most one prescription "
            "per order (DB-level 1:1 enforcement)."
        ),
    )

    # ── Patient FK ───────────────────────────────────────────────────────────
    patient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → users.id — the patient who uploaded the prescription",
    )

    # ── Pharmacist FK ────────────────────────────────────────────────────────
    pharmacist_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment=(
            "FK → users.id (Apoteker role) — NULL until a pharmacist reviews; "
            "M:1 because one pharmacist can review many prescriptions"
        ),
    )

    # ── Prescription data ─────────────────────────────────────────────────────
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Storage path of the uploaded prescription photo",
    )
    status: Mapped[PrescriptionStatus] = mapped_column(
        Enum(PrescriptionStatus, name="prescription_status_enum", create_type=True),
        nullable=False,
        server_default=PrescriptionStatus.PENDING.value,
        index=True,
        comment="Pharmacist review outcome: pending → approved / rejected",
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Pharmacist's explanation when status = REJECTED",
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp when pharmacist approved or rejected the prescription",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when the prescription was first uploaded",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    # Bidirectional 1:1 with Order
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="prescription",
        lazy="joined",
    )
    # Patient who uploaded
    patient: Mapped[User] = relationship(
        "User",
        foreign_keys=[patient_id],
        back_populates="prescriptions_as_patient",
        lazy="joined",
    )
    # Pharmacist who reviewed (may be None until reviewed)
    pharmacist: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[pharmacist_id],
        back_populates="prescriptions_as_pharmacist",
        lazy="joined",
    )

    # ── Table-level constraints ───────────────────────────────────────────────
    __table_args__ = (
        # Redundant explicit UniqueConstraint for Alembic autogenerate clarity
        UniqueConstraint("order_id", name="uq_prescriptions_order_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Prescription id={self.id} order_id={self.order_id} "
            f"status={self.status.value}>"
        )


# ══════════════════════════════════════════════════════════════════════════════
# § 8  audit_logs
# ══════════════════════════════════════════════════════════════════════════════


class AuditLog(Base):
    """
    audit_logs — Immutable activity trail for all user actions.

    Security requirements from PRD AUTH-06:
      • Every login/logout, CRUD operation, stock change, and transaction
        must produce an audit row.
      • Rows are append-only: no UPDATE or DELETE should ever be run on this table.
        Enforce this via PostgreSQL row-level security or application policy.

    JSONB columns:
      • `old_value` / `new_value` — store the before/after state of the changed
        entity as JSONB (PostgreSQL binary JSON) for efficient indexing and
        querying compared to TEXT columns.

    `created_at` is the only timestamp — there is no `updated_at` because
    audit logs must never be mutated.
    """

    __tablename__ = "audit_logs"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Audit log PK",
    )

    # ── Actor ─────────────────────────────────────────────────────────────────
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment=(
            "FK → users.id — who performed the action. "
            "Nullable so logs survive if the user account is later deleted."
        ),
    )

    # ── Action metadata ───────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "Semantic action name in SCREAMING_SNAKE_CASE, "
            "e.g. LOGIN, LOGOUT, CREATE_PRODUCT, UPDATE_STOCK, PLACE_ORDER"
        ),
    )
    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Application module that generated this log, e.g. AUTH, PRODUCT, ORDER",
    )
    target_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="ORM entity/table name of the affected record, e.g. Product, Order",
    )
    target_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="PK of the affected entity row (NULL for non-entity actions like LOGIN)",
    )

    # ── Change payload (JSONB) ────────────────────────────────────────────────
    old_value: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Serialised state of the entity BEFORE the change (JSONB)",
    )
    new_value: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Serialised state of the entity AFTER the change (JSONB)",
    )

    # ── Request context ───────────────────────────────────────────────────────
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address (supports both IPv4 and IPv6 — max 45 chars)",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full User-Agent header string from the HTTP request",
    )

    # ── Immutable timestamp ───────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="UTC timestamp when the event occurred — never mutated",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[Optional[User]] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} user_id={self.user_id} "
            f"action={self.action!r} module={self.module!r}>"
        )



