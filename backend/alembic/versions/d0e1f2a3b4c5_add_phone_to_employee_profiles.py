"""feat: agregar phone a employee_profiles

Revision ID: d0e1f2a3b4c5
Revises: c7e8d9f0a1b2
Create Date: 2026-06-28
"""
from alembic import op
import sqlalchemy as sa

revision = "d0e1f2a3b4c5"
down_revision = "c7e8d9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employee_profiles", sa.Column("phone", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("employee_profiles", "phone")
