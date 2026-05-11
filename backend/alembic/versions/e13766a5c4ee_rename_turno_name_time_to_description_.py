"""rename turno name/time to description/start_time/end_time

Revision ID: e13766a5c4ee
Revises: a7d24fc0ff77
Create Date: 2026-05-11 19:47:31.389977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e13766a5c4ee'
down_revision: Union[str, Sequence[str], None] = 'a7d24fc0ff77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('turnos', 'name', new_column_name='description')
    op.alter_column('turnos', 'time', new_column_name='start_time')
    op.add_column('turnos', sa.Column('end_time', sa.Time(), nullable=True))
    op.execute('UPDATE turnos SET end_time = start_time')
    op.alter_column('turnos', 'end_time', nullable=False)
    op.drop_constraint('uq_turno_actividad_mes_nombre', 'turnos', type_='unique')
    op.create_unique_constraint(
        'uq_turno_actividad_mes_descripcion',
        'turnos',
        ['activity_id', 'month', 'year', 'description'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_turno_actividad_mes_descripcion', 'turnos', type_='unique')
    op.create_unique_constraint(
        'uq_turno_actividad_mes_nombre',
        'turnos',
        ['activity_id', 'month', 'year', 'description'],
    )
    op.drop_column('turnos', 'end_time')
    op.alter_column('turnos', 'start_time', new_column_name='time')
    op.alter_column('turnos', 'description', new_column_name='name')
