"""add original_amount and discount_full_classes to enrollments

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('enrollments', sa.Column('original_amount', sa.Numeric(10, 2), nullable=True))
    op.add_column('enrollments', sa.Column('discount_full_classes', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('enrollments', 'discount_full_classes')
    op.drop_column('enrollments', 'original_amount')
