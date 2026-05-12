"""add app_config table with turnos_page_size

Revision ID: 6cdce46753aa
Revises: e13766a5c4ee
Create Date: 2026-05-11 20:11:12.224012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6cdce46753aa'
down_revision: Union[str, Sequence[str], None] = 'e13766a5c4ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'app_config',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )
    op.execute("INSERT INTO app_config (key, value) VALUES ('turnos_page_size', '20')")
    op.execute("INSERT INTO app_config (key, value) VALUES ('next_month_preview_days', '10')")


def downgrade() -> None:
    op.drop_table('app_config')
