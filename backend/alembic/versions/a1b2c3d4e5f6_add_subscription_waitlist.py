"""feat: agregar tabla subscription_waitlist para lista de espera de abonos

Revision ID: a1b2c3d4e5f6
Revises: f9a1b2c3d4e5
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "f9a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    waitlist_status = sa.Enum("waiting", "promoted", "cancelled", name="waitlist_status_enum")
    waitlist_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "subscription_waitlist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turno_id", sa.Integer(), sa.ForeignKey("turnos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("waiting", "promoted", "cancelled", name="waitlist_status_enum"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_subscription_waitlist_id", "id"),
        sa.Index("ix_subscription_waitlist_turno_status", "turno_id", "status"),
        sa.Index("ix_subscription_waitlist_user", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("subscription_waitlist")
    op.execute("DROP TYPE IF EXISTS waitlist_status_enum")
