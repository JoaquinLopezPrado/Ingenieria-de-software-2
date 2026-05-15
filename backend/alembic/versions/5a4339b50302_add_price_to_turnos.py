"""add_price_to_turnos

Revision ID: 5a4339b50302
Revises: 6cdce46753aa
Create Date: 2026-05-14 22:30:47.489351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a4339b50302'
down_revision: Union[str, Sequence[str], None] = '6cdce46753aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('turnos', sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.execute("UPDATE turnos SET price = 0 WHERE price IS NULL")
    op.alter_column('turnos', 'price', nullable=False)


def downgrade() -> None:
    op.drop_column('turnos', 'price')