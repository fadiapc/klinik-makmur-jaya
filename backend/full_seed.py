#!/usr/bin/env python3
"""
full_seed.py — Comprehensive data seeder for Klinik Makmur Jaya.

Creates:
  - 4 Roles: admin, apoteker, kasir, pelanggan (pasien)
  - 4 Categories: Obat Resep, Obat Bebas, Suplemen, Alat Kesehatan
  - 2 Suppliers
  - 6 Users: 1 admin, 1 apoteker, 1 kasir, 3 pelanggan (password: Password123!)
  - 20 Products (mix of semua kategori, obat bebas dan obat resep)
  - Stock batches untuk setiap produk
  - 5 Sample orders dengan berbagai status

Usage:
    cd backend
    .\.venv\Scripts\python.exe full_seed.py

CATATAN: Jika sudah pernah dijalankan, script ini aman dijalankan ulang
karena mengecek existing data sebelum insert (idempotent untuk roles/categories).
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables explicitly for the script
load_dotenv()

from app.core.config import settings
from app.models.models import (
    Role, User, Category, Supplier, Product, StockBatch,
    Order, OrderItem, OrderStatus, OrderType, PaymentMethod, PaymentStatus,
    Prescription, PrescriptionStatus,
)

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = "Password123!"


def hash_pw(pw: str) -> str:
    return pwd_context.hash(pw)


# ── DB Engine ─────────────────────────────────────────────────────────────────
engine = create_async_engine(settings.async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# ── Helper ────────────────────────────────────────────────────────────────────

async def get_or_create_role(db: AsyncSession, name: str, description: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if not role:
        role = Role(name=name, description=description)
        db.add(role)
        await db.flush()
        print(f"  ✅ Role created: {name}")
    else:
        print(f"  ⏭  Role exists: {name}")
    return role


async def get_or_create_category(db: AsyncSession, name: str, description: str) -> Category:
    result = await db.execute(select(Category).where(Category.name == name))
    cat = result.scalar_one_or_none()
    if not cat:
        cat = Category(name=name, description=description)
        db.add(cat)
        await db.flush()
        print(f"  ✅ Category created: {name}")
    else:
        print(f"  ⏭  Category exists: {name}")
    return cat


async def get_or_create_user(
    db: AsyncSession, name: str, email: str, role_id: int,
    phone: str = None
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=hash_pw(DEFAULT_PASSWORD),
            role_id=role_id,
            phone=phone,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        print(f"  ✅ User created: {email}")
    else:
        print(f"  ⏭  User exists: {email}")
    return user


async def create_product(
    db: AsyncSession, name: str, sku: str, category_id: int, supplier_id: int,
    price: float, description: str, requires_prescription: bool,
    min_stock_threshold: int = 10
) -> Product:
    result = await db.execute(select(Product).where(Product.sku == sku))
    product = result.scalar_one_or_none()
    if not product:
        product = Product(
            name=name,
            sku=sku,
            category_id=category_id,
            supplier_id=supplier_id,
            price=Decimal(str(price)),
            description=description,
            requires_prescription=requires_prescription,
            min_stock_threshold=min_stock_threshold,
            is_active=True,
        )
        db.add(product)
        await db.flush()
        print(f"  ✅ Product created: {name} (SKU: {sku})")
    else:
        print(f"  ⏭  Product exists: {sku}")
    return product


async def create_stock_batch(
    db: AsyncSession, product_id: int, batch_number: str,
    quantity: int, received_at: datetime, expiry_date: datetime,
    purchase_price: float
) -> StockBatch:
    result = await db.execute(
        select(StockBatch).where(StockBatch.batch_number == batch_number)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        batch = StockBatch(
            product_id=product_id,
            batch_number=batch_number,
            quantity=quantity,
            received_at=received_at,
            expiry_date=expiry_date,
            purchase_price=Decimal(str(purchase_price)),
        )
        db.add(batch)
        await db.flush()
    return batch


# ── Main Seeder ───────────────────────────────────────────────────────────────

async def seed():
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 60)
        print("🌱 KLINIK MAKMUR JAYA — FULL DATA SEED")
        print("=" * 60)

        # ── 1. Roles ──────────────────────────────────────────────────────────
        print("\n📋 Seeding Roles...")
        role_admin = await get_or_create_role(db, "admin", "Super admin dengan akses penuh")
        role_apoteker = await get_or_create_role(db, "apoteker", "Apoteker — verifikasi resep dan pengiriman")
        role_kasir = await get_or_create_role(db, "kasir", "Kasir — konfirmasi pembayaran")
        role_pasien = await get_or_create_role(db, "pasien", "Pelanggan / Pasien klinik")

        # ── 2. Categories ─────────────────────────────────────────────────────
        print("\n📂 Seeding Categories...")
        cat_resep = await get_or_create_category(
            db, "Obat Resep",
            "Obat keras yang hanya dapat dibeli dengan resep dokter"
        )
        cat_bebas = await get_or_create_category(
            db, "Obat Bebas",
            "Obat yang dapat dibeli tanpa resep dokter"
        )
        cat_suplemen = await get_or_create_category(
            db, "Suplemen",
            "Vitamin, mineral, dan suplemen kesehatan"
        )
        cat_alkes = await get_or_create_category(
            db, "Alat Kesehatan",
            "Peralatan medis dan alat bantu kesehatan"
        )

        # ── 3. Suppliers ──────────────────────────────────────────────────────
        print("\n🏭 Seeding Suppliers...")
        result = await db.execute(select(Supplier).where(Supplier.name == "PT Kimia Farma"))
        sup1 = result.scalar_one_or_none()
        if not sup1:
            sup1 = Supplier(
                name="PT Kimia Farma",
                contact_person="Budi Santoso",
                phone="021-5555-1234",
                email="order@kimiafarma.co.id",
                address="Jl. Veteran No. 9, Jakarta Pusat",
            )
            db.add(sup1)
            await db.flush()
            print("  ✅ Supplier: PT Kimia Farma")
        else:
            print("  ⏭  Supplier exists: PT Kimia Farma")

        result = await db.execute(select(Supplier).where(Supplier.name == "PT Kalbe Farma"))
        sup2 = result.scalar_one_or_none()
        if not sup2:
            sup2 = Supplier(
                name="PT Kalbe Farma",
                contact_person="Dewi Rahayu",
                phone="021-4444-5678",
                email="sales@kalbe.co.id",
                address="Jl. Let. Jend. Suprapto Kav. 4, Jakarta Pusat",
            )
            db.add(sup2)
            await db.flush()
            print("  ✅ Supplier: PT Kalbe Farma")
        else:
            print("  ⏭  Supplier exists: PT Kalbe Farma")

        # ── 4. Users ──────────────────────────────────────────────────────────
        print("\n👤 Seeding Users...")
        admin = await get_or_create_user(db, "Admin Klinik", "admin@klinikmakmur.id", role_admin.id, "081200000001")
        apoteker = await get_or_create_user(db, "Apt. Sari Dewi", "apoteker@klinikmakmur.id", role_apoteker.id, "081200000002")
        kasir = await get_or_create_user(db, "Kasir Rahmat", "kasir@klinikmakmur.id", role_kasir.id, "081200000003")
        pelanggan1 = await get_or_create_user(db, "Andi Wijaya", "andi@example.com", role_pasien.id, "081234567890")
        pelanggan2 = await get_or_create_user(db, "Siti Rahayu", "siti@example.com", role_pasien.id, "081234567891")
        pelanggan3 = await get_or_create_user(db, "Budi Santoso", "budi@example.com", role_pasien.id, "081234567892")

        # ── 5. Products ───────────────────────────────────────────────────────
        print("\n💊 Seeding Products...")

        # OBAT RESEP (memerlukan resep dokter)
        amox = await create_product(db, "Amoxicillin 500mg", "OBT-RX-001", cat_resep.id, sup1.id,
                                    25000, "Antibiotik untuk infeksi bakteri. Kemasan 10 kapsul.", True, 50)
        metformin = await create_product(db, "Metformin 500mg", "OBT-RX-002", cat_resep.id, sup1.id,
                                         35000, "Obat diabetes tipe 2. Kemasan 30 tablet.", True, 50)
        amlodipine = await create_product(db, "Amlodipine 5mg", "OBT-RX-003", cat_resep.id, sup2.id,
                                           45000, "Obat antihipertensi. Kemasan 30 tablet.", True, 30)
        losartan = await create_product(db, "Losartan 50mg", "OBT-RX-004", cat_resep.id, sup2.id,
                                         55000, "Obat hipertensi golongan ARB. Kemasan 30 tablet.", True, 30)
        omeprazole = await create_product(db, "Omeprazole 20mg", "OBT-RX-005", cat_resep.id, sup1.id,
                                           40000, "Obat tukak lambung. Kemasan 14 kapsul.", True, 40)

        # OBAT BEBAS (tidak memerlukan resep)
        paracetamol = await create_product(db, "Paracetamol 500mg (Generik)", "OBT-BB-001", cat_bebas.id, sup1.id,
                                             8000, "Analgesik dan antipiretik. Kemasan 12 tablet.", False, 100)
        antasida = await create_product(db, "Antasida Doen", "OBT-BB-002", cat_bebas.id, sup1.id,
                                          12000, "Obat maag dan kembung. Kemasan 12 tablet kunyah.", False, 80)
        ctm = await create_product(db, "CTM (Chlorpheniramine Maleat)", "OBT-BB-003", cat_bebas.id, sup2.id,
                                     5000, "Antihistamin untuk alergi ringan. Kemasan 12 tablet.", False, 100)
        oralit = await create_product(db, "Oralit 200ml Jeruk", "OBT-BB-004", cat_bebas.id, sup1.id,
                                        6000, "Rehidrasi oral untuk diare. Sachet bubuk 1 liter.", False, 120)
        betadin = await create_product(db, "Betadine Antiseptik 60ml", "OBT-BB-005", cat_bebas.id, sup2.id,
                                         28000, "Cairan antiseptik povidone-iodine 10%.", False, 60)

        # SUPLEMEN
        vitc = await create_product(db, "Vitamin C 1000mg Effervescent", "SUP-001", cat_suplemen.id, sup2.id,
                                      45000, "Suplemen imunitas harian. Rasa jeruk. Isi 10 tablet.", False, 50)
        vitd = await create_product(db, "Vitamin D3 1000 IU", "SUP-002", cat_suplemen.id, sup2.id,
                                      85000, "Suplemen tulang dan imun. Isi 60 kapsul lunak.", False, 40)
        omega3 = await create_product(db, "Omega-3 Fish Oil 1000mg", "SUP-003", cat_suplemen.id, sup2.id,
                                        120000, "Suplemen kesehatan jantung dan otak. Isi 30 kapsul.", False, 30)
        multivit = await create_product(db, "Multivitamin Dewasa Lengkap", "SUP-004", cat_suplemen.id, sup1.id,
                                          75000, "Suplemen vitamin dan mineral lengkap. Isi 30 tablet.", False, 50)
        probiotik = await create_product(db, "Probiotik Lacto-B", "SUP-005", cat_suplemen.id, sup2.id,
                                           55000, "Probiotik untuk kesehatan pencernaan. Isi 30 sachet.", False, 40)

        # ALAT KESEHATAN
        tensi = await create_product(db, "Tensimeter Digital Omron HEM-7120", "ALKES-001", cat_alkes.id, sup2.id,
                                       350000, "Tensimeter digital otomatis untuk lengan atas. Akurasi tinggi.", False, 5)
        termometer = await create_product(db, "Termometer Digital Inframerah", "ALKES-002", cat_alkes.id, sup1.id,
                                            180000, "Termometer non-kontak untuk pengukuran suhu cepat.", False, 10)
        masker = await create_product(db, "Masker Medis 3-Ply (50 pcs)", "ALKES-003", cat_alkes.id, sup1.id,
                                        35000, "Masker medis disposable 3 lapis. Isi 50 lembar per box.", False, 30)
        glukotest = await create_product(db, "Strip Gula Darah GlucoTest (50 strips)", "ALKES-004", cat_alkes.id, sup2.id,
                                          150000, "Strip tes gula darah. Kompatibel dengan alat GlucoTest series.", False, 20)
        nebulizer = await create_product(db, "Nebulizer Compressor Omron", "ALKES-005", cat_alkes.id, sup2.id,
                                          650000, "Alat nebulisasi untuk terapi pernafasan. Lengkap dengan masker.", False, 3)

        # ── 6. Stock Batches ──────────────────────────────────────────────────
        print("\n📦 Seeding Stock Batches...")
        now = datetime.now(timezone.utc)
        products_with_batches = [
            (amox, [("BATCH-AMX-001", 200, 24), ("BATCH-AMX-002", 150, 18)]),
            (metformin, [("BATCH-MET-001", 300, 24)]),
            (amlodipine, [("BATCH-AML-001", 200, 20)]),
            (losartan, [("BATCH-LOS-001", 150, 22)]),
            (omeprazole, [("BATCH-OMP-001", 180, 18)]),
            (paracetamol, [("BATCH-PCT-001", 500, 24), ("BATCH-PCT-002", 300, 12)]),
            (antasida, [("BATCH-ANT-001", 400, 18)]),
            (ctm, [("BATCH-CTM-001", 600, 24)]),
            (oralit, [("BATCH-ORL-001", 800, 24)]),
            (betadin, [("BATCH-BTD-001", 200, 18)]),
            (vitc, [("BATCH-VTC-001", 250, 12)]),
            (vitd, [("BATCH-VTD-001", 200, 24)]),
            (omega3, [("BATCH-OMG-001", 150, 18)]),
            (multivit, [("BATCH-MLT-001", 200, 24)]),
            (probiotik, [("BATCH-PRB-001", 180, 12)]),
            (tensi, [("BATCH-TNS-001", 20, 36)]),
            (termometer, [("BATCH-TRM-001", 50, 24)]),
            (masker, [("BATCH-MSK-001", 300, 24)]),
            (glukotest, [("BATCH-GLK-001", 100, 12)]),
            (nebulizer, [("BATCH-NBL-001", 10, 36)]),
        ]
        for product, batches in products_with_batches:
            for i, (batch_num, qty, months_expiry) in enumerate(batches):
                received_at = now - timedelta(days=30 * i)
                expiry_date = now + timedelta(days=30 * months_expiry)
                await create_stock_batch(
                    db, product.id, batch_num, qty,
                    received_at, expiry_date,
                    float(product.price) * 0.6
                )
        print(f"  ✅ Stock batches seeded for all products")

        # ── 7. Sample Orders ──────────────────────────────────────────────────
        print("\n🛒 Seeding Sample Orders...")

        # Helper to generate order code
        order_count = 0
        def next_order_code():
            nonlocal order_count
            order_count += 1
            return f"ORD-{now.strftime('%Y%m%d')}-{order_count:04d}"

        # Check if sample orders already exist
        result = await db.execute(select(Order).limit(1))
        existing_order = result.scalar_one_or_none()

        if not existing_order:
            # Order 1: Pelanggan1 — Status SELESAI (obat bebas)
            o1 = Order(
                order_code=next_order_code(),
                user_id=pelanggan1.id,
                order_type=OrderType.ONLINE,
                payment_method=PaymentMethod.TRANSFER,
                subtotal=Decimal("53000"),
                discount=Decimal("0"),
                tax=Decimal("5830"),
                grand_total=Decimal("58830"),
                status=OrderStatus.SELESAI,
                payment_status=PaymentStatus.PAID,
                notes="Tolong kirim ke alamat rumah",
                created_at=now - timedelta(days=7),
            )
            db.add(o1)
            await db.flush()
            db.add_all([
                OrderItem(order_id=o1.id, product_id=paracetamol.id, quantity=3, unit_price=Decimal("8000"), subtotal=Decimal("24000")),
                OrderItem(order_id=o1.id, product_id=vitc.id, quantity=1, unit_price=Decimal("45000"), subtotal=Decimal("45000")),
            ])

            # Order 2: Pelanggan2 — Status MENUNGGU_VERIFIKASI_RESEP (obat keras)
            o2 = Order(
                order_code=next_order_code(),
                user_id=pelanggan2.id,
                order_type=OrderType.ONLINE,
                payment_method=PaymentMethod.TRANSFER,
                subtotal=Decimal("25000"),
                discount=Decimal("0"),
                tax=Decimal("2750"),
                grand_total=Decimal("27750"),
                status=OrderStatus.MENUNGGU_VERIFIKASI_RESEP,
                payment_status=PaymentStatus.UNPAID,
                created_at=now - timedelta(hours=3),
            )
            db.add(o2)
            await db.flush()
            db.add(OrderItem(order_id=o2.id, product_id=amox.id, quantity=1, unit_price=Decimal("25000"), subtotal=Decimal("25000")))
            # Prescription for o2
            db.add(Prescription(
                order_id=o2.id,
                patient_id=pelanggan2.id,
                image_url="prescriptions/sample/sample_rx.jpg",
                status=PrescriptionStatus.PENDING,
            ))

            # Order 3: Pelanggan3 — Status MENUNGGU_PEMBAYARAN (obat bebas, sudah dikonfirmasi)
            o3 = Order(
                order_code=next_order_code(),
                user_id=pelanggan3.id,
                order_type=OrderType.ONLINE,
                payment_method=PaymentMethod.TRANSFER,
                subtotal=Decimal("85000"),
                discount=Decimal("0"),
                tax=Decimal("9350"),
                grand_total=Decimal("94350"),
                status=OrderStatus.MENUNGGU_PEMBAYARAN,
                payment_status=PaymentStatus.UNPAID,
                payment_deadline=now + timedelta(hours=20),
                created_at=now - timedelta(hours=5),
            )
            db.add(o3)
            await db.flush()
            db.add(OrderItem(order_id=o3.id, product_id=vitd.id, quantity=1, unit_price=Decimal("85000"), subtotal=Decimal("85000")))

            # Order 4: Pelanggan1 — Status DIPROSES (sudah bayar dan kasir konfirmasi)
            o4 = Order(
                order_code=next_order_code(),
                user_id=pelanggan1.id,
                order_type=OrderType.ONLINE,
                payment_method=PaymentMethod.QRIS,
                subtotal=Decimal("180000"),
                discount=Decimal("0"),
                tax=Decimal("19800"),
                grand_total=Decimal("199800"),
                status=OrderStatus.DIPROSES,
                payment_status=PaymentStatus.PAID,
                created_at=now - timedelta(days=1),
            )
            db.add(o4)
            await db.flush()
            db.add(OrderItem(order_id=o4.id, product_id=termometer.id, quantity=1, unit_price=Decimal("180000"), subtotal=Decimal("180000")))

            # Order 5: Pelanggan2 — Status DIBATALKAN (resep ditolak)
            o5 = Order(
                order_code=next_order_code(),
                user_id=pelanggan2.id,
                order_type=OrderType.ONLINE,
                payment_method=PaymentMethod.TRANSFER,
                subtotal=Decimal("55000"),
                discount=Decimal("0"),
                tax=Decimal("6050"),
                grand_total=Decimal("61050"),
                status=OrderStatus.DIBATALKAN,
                payment_status=PaymentStatus.UNPAID,
                notes="Dibatalkan — resep ditolak",
                created_at=now - timedelta(days=3),
            )
            db.add(o5)
            await db.flush()
            db.add(OrderItem(order_id=o5.id, product_id=losartan.id, quantity=1, unit_price=Decimal("55000"), subtotal=Decimal("55000")))
            db.add(Prescription(
                order_id=o5.id,
                patient_id=pelanggan2.id,
                pharmacist_id=apoteker.id,
                image_url="prescriptions/sample/sample_rx_rejected.jpg",
                status=PrescriptionStatus.REJECTED,
                rejection_reason="Resep tidak terbaca dengan jelas dan tidak ada stempel dokter.",
                verified_at=now - timedelta(days=2),
            ))

            await db.flush()
            print("  ✅ 5 sample orders created")
        else:
            print("  ⏭  Orders already exist, skipping sample orders")

        await db.commit()
        print("\n" + "=" * 60)
        print("✅ SEED COMPLETE!")
        print("=" * 60)
        print(f"\n🔑 Login Credentials (password: {DEFAULT_PASSWORD}):")
        print("   admin@klinikmakmur.id       → Admin")
        print("   apoteker@klinikmakmur.id    → Apoteker")
        print("   kasir@klinikmakmur.id       → Kasir")
        print("   andi@example.com            → Pelanggan 1")
        print("   siti@example.com            → Pelanggan 2")
        print("   budi@example.com            → Pelanggan 3")
        print()


if __name__ == "__main__":
    asyncio.run(seed())
