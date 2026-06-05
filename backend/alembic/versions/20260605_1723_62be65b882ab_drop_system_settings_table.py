"""Drop system_settings table

Revision ID: 62be65b882ab
Revises: 48b761d17260
Create Date: 2026-06-05 17:23:57.661243
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62be65b882ab'
down_revision: Union[str, None] = '48b761d17260'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('system_settings')


def downgrade() -> None:
    pass
