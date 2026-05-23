"""agrega contexto snapshot a payments

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-05-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('payments', sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id'), nullable=True))
    op.add_column('payments', sa.Column('activity_name_snapshot', sa.String(), nullable=False, server_default=''))
    op.add_column('payments', sa.Column('month_snapshot', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('payments', sa.Column('year_snapshot', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('payments', sa.Column('enrollment_type_snapshot', sa.String(), nullable=False, server_default='monthly'))
    op.alter_column('payments', 'activity_name_snapshot', server_default=None)
    op.alter_column('payments', 'month_snapshot', server_default=None)
    op.alter_column('payments', 'year_snapshot', server_default=None)
    op.alter_column('payments', 'enrollment_type_snapshot', server_default=None)


def downgrade() -> None:
    op.drop_column('payments', 'enrollment_type_snapshot')
    op.drop_column('payments', 'year_snapshot')
    op.drop_column('payments', 'month_snapshot')
    op.drop_column('payments', 'activity_name_snapshot')
    op.drop_column('payments', 'activity_id')
