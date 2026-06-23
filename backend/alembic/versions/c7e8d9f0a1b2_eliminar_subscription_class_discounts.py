"""eliminar subscription_class_discounts

Revision ID: c7e8d9f0a1b2
Revises: a9b8c7d6e5f4
Create Date: 2026-06-23 00:00:01.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c7e8d9f0a1b2'
down_revision: Union[str, None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('subscription_class_discounts')


def downgrade() -> None:
    op.create_table(
        'subscription_class_discounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('source_clase_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('applied_to_charge_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_clase_id'], ['clases.id']),
        sa.ForeignKeyConstraint(['applied_to_charge_id'], ['subscription_charges.id']),
        sa.PrimaryKeyConstraint('id'),
    )
