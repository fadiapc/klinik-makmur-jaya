"""Enable pg_trgm for fuzzy search

Revision ID: 48b761d17260
Revises: 979fa69717d4
Create Date: 2026-06-05 04:54:52.997169
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48b761d17260'
down_revision: Union[str, None] = '979fa69717d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    pass


def downgrade() -> None:
    # Disable pg_trgm extension
    op.execute('DROP EXTENSION IF EXISTS pg_trgm;')
    pass
