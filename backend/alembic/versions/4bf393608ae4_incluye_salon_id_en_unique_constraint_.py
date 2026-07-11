"""incluye salon_id en unique constraint de turnos

Revision ID: 4bf393608ae4
Revises: 5f3e0656162f
Create Date: 2026-07-11 15:08:15.271287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bf393608ae4'
down_revision: Union[str, Sequence[str], None] = '5f3e0656162f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('uq_turno_actividad_descripcion_horario'), 'turnos', type_='unique')
    op.create_unique_constraint('uq_turno_actividad_descripcion_horario', 'turnos', ['activity_id', 'description', 'start_time', 'end_time', 'salon_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_turno_actividad_descripcion_horario', 'turnos', type_='unique')
    op.create_unique_constraint(op.f('uq_turno_actividad_descripcion_horario'), 'turnos', ['activity_id', 'description', 'start_time', 'end_time'], postgresql_nulls_not_distinct=False)
