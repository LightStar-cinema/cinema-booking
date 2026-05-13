"""add_promo_code_to_bookings

Revision ID: b3f9a1c2d4e5
Revises: 35cbc24e64b9
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3f9a1c2d4e5'
down_revision: Union[str, None] = '35cbc24e64b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('bookings', sa.Column('promo_code', sa.String(20), nullable=True))
    op.add_column('bookings', sa.Column('original_amount', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('bookings', 'promo_code')
    op.drop_column('bookings', 'original_amount')
