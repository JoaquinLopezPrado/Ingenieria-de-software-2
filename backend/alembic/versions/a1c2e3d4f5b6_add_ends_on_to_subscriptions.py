"""add ends_on a subscriptions (baja programada al fin del período pagado)

Revision ID: a1c2e3d4f5b6
Revises: f9a1b2c3d4e5
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa

revision = "a1c2e3d4f5b6"
down_revision = "f9a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("ends_on", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("subscriptions", "ends_on")
