"""unicidad turno_id+date para clases activas

Revision ID: e08e0a4a2947
Revises: 4bf393608ae4
Create Date: 2026-07-11 16:25:24.350671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e08e0a4a2947'
down_revision: Union[str, Sequence[str], None] = '4bf393608ae4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('uq_clases_turno_date_active', 'clases', ['turno_id', 'date'], unique=True, postgresql_where=sa.text('is_active = TRUE'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_clases_turno_date_active', table_name='clases', postgresql_where=sa.text('is_active = TRUE'))
