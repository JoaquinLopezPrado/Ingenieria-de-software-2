"""Agrego gender al client_profiles

Revision ID: 20d89ee06a37
Revises: 215d7870bef9
Create Date: 2026-04-29 17:11:19.480845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20d89ee06a37'
down_revision: Union[str, Sequence[str], None] = '215d7870bef9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


gender_enum = sa.Enum('masculino', 'femenino', name='gender_enum')


def upgrade() -> None:
    """Upgrade schema."""
    gender_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('client_profiles', sa.Column('gender', gender_enum, nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('client_profiles', 'gender')
    gender_enum.drop(op.get_bind(), checkfirst=True)
