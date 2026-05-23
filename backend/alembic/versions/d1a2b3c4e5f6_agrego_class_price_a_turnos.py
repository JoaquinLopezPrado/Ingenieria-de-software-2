"""agrego class_price a turnos

Revision ID: d1a2b3c4e5f6
Revises: b8d1f4a2e093
Create Date: 2026-05-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd1a2b3c4e5f6'
down_revision: Union[str, None] = 'b8d1f4a2e093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('turnos', sa.Column('class_price', sa.Numeric(10, 2), nullable=True))
    op.execute('UPDATE turnos SET class_price = price')
    op.alter_column('turnos', 'class_price', nullable=False)


def downgrade() -> None:
    op.drop_column('turnos', 'class_price')
