"""snapshot de horario en clases

Revision ID: a9b8c7d6e5f4
Revises: 1c2764022b98
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, None] = '1c2764022b98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clases', sa.Column('start_time', sa.Time(), nullable=True))
    op.add_column('clases', sa.Column('end_time', sa.Time(), nullable=True))
    op.execute(
        'UPDATE clases SET start_time = t.start_time, end_time = t.end_time '
        'FROM turnos t WHERE clases.turno_id = t.id'
    )
    op.alter_column('clases', 'start_time', nullable=False)
    op.alter_column('clases', 'end_time', nullable=False)


def downgrade() -> None:
    op.drop_column('clases', 'end_time')
    op.drop_column('clases', 'start_time')
