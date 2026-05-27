"""add excluded_sin_cupo_count and excluded_ya_inscripto_count to enrollments

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("enrollments", sa.Column("excluded_sin_cupo_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("enrollments", sa.Column("excluded_ya_inscripto_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("enrollments", "excluded_ya_inscripto_count")
    op.drop_column("enrollments", "excluded_sin_cupo_count")
