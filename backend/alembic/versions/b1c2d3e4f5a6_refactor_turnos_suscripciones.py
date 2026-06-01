"""refactor: turnos indefinidos y suscripciones mensuales

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-05-31 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- turnos: eliminar month, year, price y actualizar unique constraint ---
    op.drop_constraint("uq_turno_actividad_mes_descripcion", "turnos", type_="unique")
    op.drop_column("turnos", "month")
    op.drop_column("turnos", "year")
    op.drop_column("turnos", "price")
    op.create_unique_constraint(
        "uq_turno_actividad_descripcion_horario",
        "turnos",
        ["activity_id", "description", "start_time", "end_time"],
    )

    # --- enrollments: renombrar tipo MONTHLY → SUBSCRIPTION ---
    op.execute("ALTER TYPE enrollment_type_enum RENAME VALUE 'monthly' TO 'subscription'")

    # --- enrollments: eliminar campos de descuento, agregar last_payment_date ---
    op.drop_column("enrollments", "excluded_sin_cupo_count")
    op.drop_column("enrollments", "excluded_ya_inscripto_count")
    op.add_column("enrollments", sa.Column("last_payment_date", sa.Date(), nullable=True))

    # --- payments: eliminar unique constraint en enrollment_id ---
    op.drop_constraint("payments_enrollment_id_key", "payments", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("payments_enrollment_id_key", "payments", ["enrollment_id"])

    op.drop_column("enrollments", "last_payment_date")
    op.add_column("enrollments", sa.Column("excluded_ya_inscripto_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("enrollments", sa.Column("excluded_sin_cupo_count", sa.Integer(), nullable=False, server_default="0"))

    op.execute("ALTER TYPE enrollment_type_enum RENAME VALUE 'subscription' TO 'monthly'")

    op.drop_constraint("uq_turno_actividad_descripcion_horario", "turnos", type_="unique")
    op.add_column("turnos", sa.Column("price", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("turnos", sa.Column("year", sa.Integer(), nullable=False, server_default="2026"))
    op.add_column("turnos", sa.Column("month", sa.Integer(), nullable=False, server_default="1"))
    op.create_unique_constraint(
        "uq_turno_actividad_mes_descripcion",
        "turnos",
        ["activity_id", "month", "year", "description"],
    )
