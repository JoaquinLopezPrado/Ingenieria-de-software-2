"""agrega seña a enrollments

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-06-13

"""
from typing import Union, Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'd3e4f5a6b7c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE enrollment_status_enum ADD VALUE IF NOT EXISTS 'deposit_paid'")
    op.execute("ALTER TYPE enrollment_status_enum ADD VALUE IF NOT EXISTS 'deposit_forfeited'")
    op.execute("ALTER TYPE enrollment_status_enum ADD VALUE IF NOT EXISTS 'refunded'")

    op.add_column('enrollments', sa.Column('deposit_amount', sa.Numeric(10, 2), nullable=True))
    op.add_column('enrollments', sa.Column('deposit_payment_id', sa.String(), nullable=True))
    op.add_column('enrollments', sa.Column('refund_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('enrollments', 'refund_id')
    op.drop_column('enrollments', 'deposit_payment_id')
    op.drop_column('enrollments', 'deposit_amount')
    # PostgreSQL no permite eliminar valores de un enum; el downgrade no revierte los nuevos estados
