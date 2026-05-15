"""activity_description_turno_instructor

Revision ID: c33c037d718d
Revises: 5a4339b50302
Create Date: 2026-05-14 22:48:35.018217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c33c037d718d'
down_revision: Union[str, Sequence[str], None] = '5a4339b50302'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('description', sa.String(), nullable=True))
    op.execute("UPDATE activities SET description = '' WHERE description IS NULL")
    op.alter_column('activities', 'description', nullable=False)
    op.drop_column('activities', 'instructor')

    op.add_column('turnos', sa.Column('instructor', sa.String(), nullable=True))
    op.execute("UPDATE turnos SET instructor = '' WHERE instructor IS NULL")
    op.alter_column('turnos', 'instructor', nullable=False)


def downgrade() -> None:
    op.drop_column('turnos', 'instructor')
    op.add_column('activities', sa.Column('instructor', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.execute("UPDATE activities SET instructor = '' WHERE instructor IS NULL")
    op.alter_column('activities', 'instructor', nullable=False)
    op.drop_column('activities', 'description')
