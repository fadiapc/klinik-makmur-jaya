"""refactor_order_status_enum_and_add_payment_fields

Refactors the order_status_enum PostgreSQL enum type:
  OLD: pending, confirmed, processing, ready, completed, cancelled
  NEW: menunggu_verifikasi_resep, menunggu_pembayaran, menunggu_konfirmasi_kasir,
       diproses, dikirim, selesai, dibatalkan

Also adds 3 new columns to the orders table:
  - payment_proof_url   VARCHAR(500)  — URL bukti transfer dari pelanggan
  - tracking_number     VARCHAR(100)  — Nomor resi pengiriman dari Apoteker
  - payment_deadline    TIMESTAMPTZ   — Batas waktu pembayaran (auto-cancel)

Revision ID: d969d21acc3b
Revises: 62be65b882ab
Create Date: 2026-06-05 18:29:24.158380
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd969d21acc3b'
down_revision: Union[str, None] = '62be65b882ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mapping old status values → new status values (for data migration)
STATUS_MIGRATION_MAP = {
    'pending': 'menunggu_verifikasi_resep',
    'confirmed': 'menunggu_pembayaran',
    'processing': 'diproses',
    'ready': 'dikirim',
    'completed': 'selesai',
    'cancelled': 'dibatalkan',
}

OLD_STATUSES = ['pending', 'confirmed', 'processing', 'ready', 'completed', 'cancelled']
NEW_STATUSES = [
    'menunggu_verifikasi_resep',
    'menunggu_pembayaran',
    'menunggu_konfirmasi_kasir',
    'diproses',
    'dikirim',
    'selesai',
    'dibatalkan',
]


def upgrade() -> None:
    # Step 1: Convert column to TEXT to allow free data modification
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE TEXT")

    # Step 2: Migrate existing data to new status values
    for old_val, new_val in STATUS_MIGRATION_MAP.items():
        op.execute(
            f"UPDATE orders SET status = '{new_val}' WHERE status = '{old_val}'"
        )

    # Step 3: Drop the column default first (needed before dropping enum type)
    op.execute("ALTER TABLE orders ALTER COLUMN status DROP DEFAULT")

    # Step 4: Drop old enum type and recreate with new values
    op.execute("DROP TYPE IF EXISTS order_status_enum")
    new_enum_values = ", ".join(f"'{v}'" for v in NEW_STATUSES)
    op.execute(f"CREATE TYPE order_status_enum AS ENUM ({new_enum_values})")

    # Step 5: Convert column back to the new enum type
    op.execute(
        "ALTER TABLE orders ALTER COLUMN status "
        "TYPE order_status_enum USING status::order_status_enum"
    )

    # Step 6: Restore server default to new value
    op.execute(
        "ALTER TABLE orders ALTER COLUMN status "
        "SET DEFAULT 'menunggu_pembayaran'::order_status_enum"
    )

    # Step 7: Add 3 new columns
    op.add_column('orders', sa.Column(
        'payment_proof_url',
        sa.String(500),
        nullable=True,
        comment='Relative path to customer-uploaded payment proof image',
    ))
    op.add_column('orders', sa.Column(
        'tracking_number',
        sa.String(100),
        nullable=True,
        comment='Courier tracking number entered by Apoteker when shipping',
    ))
    op.add_column('orders', sa.Column(
        'payment_deadline',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='UTC deadline for payment — order auto-cancelled if exceeded (1x24h)',
    ))


def downgrade() -> None:
    # Remove new columns
    op.drop_column('orders', 'payment_deadline')
    op.drop_column('orders', 'tracking_number')
    op.drop_column('orders', 'payment_proof_url')

    # Revert enum: TEXT first
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE TEXT")

    # Reverse-map new → old
    reverse_map = {v: k for k, v in STATUS_MIGRATION_MAP.items()}
    for new_val, old_val in reverse_map.items():
        op.execute(
            f"UPDATE orders SET status = '{old_val}' WHERE status = '{new_val}'"
        )

    # Recreate old enum
    op.execute("DROP TYPE IF EXISTS order_status_enum")
    old_enum_values = ", ".join(f"'{v}'" for v in OLD_STATUSES)
    op.execute(f"CREATE TYPE order_status_enum AS ENUM ({old_enum_values})")

    op.execute(
        "ALTER TABLE orders ALTER COLUMN status "
        "TYPE order_status_enum USING status::order_status_enum"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN status "
        "SET DEFAULT 'pending'::order_status_enum"
    )
