"""refactor: separar subscriptions, subscription_charges, single_enrollments, attendances

Reemplaza el modelo de tabla `enrollments` única por entidades separadas. Reset de
esquema (los datos de inscripciones/pagos se regeneran con seeds + uso normal).

Revision ID: f9a1b2c3d4e5
Revises: e4f5a6b7c8d9
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f9a1b2c3d4e5"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Drop del modelo viejo (payments referencia enrollments) ---
    op.drop_table("payments")
    op.drop_table("enrollment_slots")
    op.drop_table("enrollments")
    op.execute("DROP TYPE IF EXISTS enrollment_status_enum")
    op.execute("DROP TYPE IF EXISTS enrollment_type_enum")

    subscription_status = sa.Enum("pending", "active", "paused", "cancelled", name="subscription_status_enum")
    charge_status = sa.Enum("pending", "paid", "overdue", "waived", name="charge_status_enum")
    single_status = sa.Enum(
        "pending", "confirmed", "cancelled", "deposit_paid", "deposit_forfeited", "refunded",
        name="single_enrollment_status_enum",
    )
    attendance_status = sa.Enum("presente", "ausente", name="attendance_status_enum")

    # --- subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("turno_id", sa.Integer(), sa.ForeignKey("turnos.id"), nullable=False),
        sa.Column("status", subscription_status, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- subscription_charges ---
    op.create_table(
        "subscription_charges",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("original_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", charge_status, nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_id", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("subscription_id", "period_month", "period_year", name="uq_charge_subscription_period"),
    )

    # --- single_enrollments ---
    op.create_table(
        "single_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("turno_id", sa.Integer(), sa.ForeignKey("turnos.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", single_status, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_id", sa.String(), nullable=True),
        sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("deposit_payment_id", sa.String(), nullable=True),
        sa.Column("refund_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- single_enrollment_slots ---
    op.create_table(
        "single_enrollment_slots",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("enrollment_id", sa.Integer(), sa.ForeignKey("single_enrollments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clase_id", sa.Integer(), sa.ForeignKey("clases.id"), nullable=False),
    )

    # --- attendances ---
    op.create_table(
        "attendances",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("clase_id", sa.Integer(), sa.ForeignKey("clases.id"), nullable=False),
        sa.Column("status", attendance_status, nullable=False),
        sa.Column("marked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "clase_id", name="uq_attendance_user_clase"),
    )

    # --- payments (recreada con FKs nuevas) ---
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("subscription_charge_id", sa.Integer(), sa.ForeignKey("subscription_charges.id"), nullable=True),
        sa.Column("single_enrollment_id", sa.Integer(), sa.ForeignKey("single_enrollments.id"), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("class_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("num_classes_snapshot", sa.Integer(), nullable=False),
        sa.Column("payment_provider_id", sa.String(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id"), nullable=True),
        sa.Column("activity_name_snapshot", sa.String(), nullable=False),
        sa.Column("month_snapshot", sa.Integer(), nullable=False),
        sa.Column("year_snapshot", sa.Integer(), nullable=False),
        sa.Column("source_type_snapshot", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("attendances")
    op.drop_table("single_enrollment_slots")
    op.drop_table("single_enrollments")
    op.drop_table("subscription_charges")
    op.drop_table("subscriptions")
    op.execute("DROP TYPE IF EXISTS attendance_status_enum")
    op.execute("DROP TYPE IF EXISTS single_enrollment_status_enum")
    op.execute("DROP TYPE IF EXISTS charge_status_enum")
    op.execute("DROP TYPE IF EXISTS subscription_status_enum")

    # Recrear esquema viejo mínimo para poder revertir (sin datos).
    enrollment_type = postgresql.ENUM("subscription", "single", name="enrollment_type_enum")
    enrollment_status = postgresql.ENUM(
        "pending", "confirmed", "cancelled", "deposit_paid", "deposit_forfeited", "refunded",
        name="enrollment_status_enum",
    )
    op.create_table(
        "enrollments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("turno_id", sa.Integer(), sa.ForeignKey("turnos.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("enrollment_type", enrollment_type, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("original_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("discount_full_classes", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", enrollment_status, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_id", sa.String(), nullable=True),
        sa.Column("last_payment_date", sa.Date(), nullable=True),
        sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("deposit_payment_id", sa.String(), nullable=True),
        sa.Column("refund_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "enrollment_slots",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("enrollment_id", sa.Integer(), sa.ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clase_id", sa.Integer(), sa.ForeignKey("clases.id"), nullable=False),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("enrollment_id", sa.Integer(), sa.ForeignKey("enrollments.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("class_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("num_classes_snapshot", sa.Integer(), nullable=False),
        sa.Column("payment_provider_id", sa.String(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id"), nullable=True),
        sa.Column("activity_name_snapshot", sa.String(), nullable=False),
        sa.Column("month_snapshot", sa.Integer(), nullable=False),
        sa.Column("year_snapshot", sa.Integer(), nullable=False),
        sa.Column("enrollment_type_snapshot", enrollment_type, nullable=False),
    )
