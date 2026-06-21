"""feat: agregar cancelación de clase, créditos y descuentos de suscripción

Revision ID: c3d4e5f6a7b8
Revises: a1c2e3d4f5b6
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "a1c2e3d4f5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── clases: campos de cancelación ──────────────────────────────────────
    op.add_column("clases", sa.Column("cancelled_reason", sa.String(), nullable=True))
    op.add_column("clases", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("clases", sa.Column("cancelled_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_clases_cancelled_by_id", "clases", "users", ["cancelled_by_id"], ["id"]
    )

    # ── class_credits: crédito por clase individual pagada en su totalidad ─
    op.create_table(
        "class_credits",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("turno_id", sa.Integer(), sa.ForeignKey("turnos.id"), nullable=False),
        sa.Column("source_clase_id", sa.Integer(), sa.ForeignKey("clases.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_for_clase_id", sa.Integer(), sa.ForeignKey("clases.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── subscription_class_discounts: descuento por cancelación para abonados mensuales ─
    op.create_table(
        "subscription_class_discounts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_clase_id", sa.Integer(), sa.ForeignKey("clases.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("applied_to_charge_id", sa.Integer(), sa.ForeignKey("subscription_charges.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("subscription_class_discounts")
    op.drop_table("class_credits")
    op.drop_constraint("fk_clases_cancelled_by_id", "clases", type_="foreignkey")
    op.drop_column("clases", "cancelled_by_id")
    op.drop_column("clases", "cancelled_at")
    op.drop_column("clases", "cancelled_reason")
