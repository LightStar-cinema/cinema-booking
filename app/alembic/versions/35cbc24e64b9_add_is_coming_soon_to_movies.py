"""add_is_coming_soon_to_movies

Revision ID: 35cbc24e64b9
Revises: 6186e1fa4a22
Create Date: 2026-05-13 06:22:47.382697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '35cbc24e64b9'
down_revision: Union[str, None] = '6186e1fa4a22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default backfills existing rows with FALSE before adding NOT NULL constraint
    op.add_column('movies', sa.Column(
        'is_coming_soon', sa.Boolean(),
        nullable=False,
        server_default=sa.text('false'),
    ))
    op.alter_column('movies', 'is_coming_soon', server_default=None)


def downgrade() -> None:
    op.drop_column('movies', 'is_coming_soon')
