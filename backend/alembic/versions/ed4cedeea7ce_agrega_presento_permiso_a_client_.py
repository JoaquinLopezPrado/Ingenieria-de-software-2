"""agrega presento_permiso a client_profiles

Revision ID: ed4cedeea7ce
Revises: d0e1f2a3b4c5
Create Date: 2026-07-03 01:34:26.895158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed4cedeea7ce'
down_revision: Union[str, Sequence[str], None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'client_profiles',
        sa.Column('presento_permiso', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('client_profiles', 'presento_permiso')
