"""agrego tabla payments

Revision ID: e2f3a4b5c6d7
Revises: d1a2b3c4e5f6
Create Date: 2026-05-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1a2b3c4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('class_price_snapshot', sa.Numeric(10, 2), nullable=False),
        sa.Column('num_classes_snapshot', sa.Integer(), nullable=False),
        sa.Column('payment_provider_id', sa.String(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('enrollment_id'),
    )


def downgrade() -> None:
    op.drop_table('payments')
