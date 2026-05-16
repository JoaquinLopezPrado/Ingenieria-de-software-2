"""refactor enrollments: turno_id, enrollment_type, amount + tabla enrollment_slots

Revision ID: b8d1f4a2e093
Revises: f3a9e2b7c104
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8d1f4a2e093"
down_revision: Union[str, Sequence[str], None] = "f3a9e2b7c104"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Vaciar enrollments para poder modificar columnas sin conflictos de FK/NOT NULL
    op.execute("DELETE FROM enrollments")

    # 2. Agregar enrollment_type_enum y las columnas nuevas
    op.execute("CREATE TYPE enrollment_type_enum AS ENUM ('monthly', 'single')")

    op.add_column("enrollments", sa.Column("turno_id", sa.Integer(), nullable=False))
    op.add_column(
        "enrollments",
        sa.Column(
            "enrollment_type",
            sa.Enum("monthly", "single", name="enrollment_type_enum", create_type=False),
            nullable=False,
        ),
    )
    op.add_column("enrollments", sa.Column("amount", sa.Numeric(10, 2), nullable=False))

    op.create_foreign_key(
        "fk_enrollments_turno_id",
        "enrollments",
        "turnos",
        ["turno_id"],
        ["id"],
    )

    # 3. Quitar la FK vieja y la columna clase_id
    op.drop_constraint("enrollments_clase_id_fkey", "enrollments", type_="foreignkey")
    op.drop_column("enrollments", "clase_id")

    # 4. Crear tabla enrollment_slots
    op.create_table(
        "enrollment_slots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enrollment_id", sa.Integer(), nullable=False),
        sa.Column("clase_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clase_id"], ["clases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_enrollment_slots_id"), "enrollment_slots", ["id"], unique=False)
    op.create_index("ix_enrollment_slots_enrollment_id", "enrollment_slots", ["enrollment_id"], unique=False)
    op.create_index("ix_enrollment_slots_clase_id", "enrollment_slots", ["clase_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_enrollment_slots_clase_id", table_name="enrollment_slots")
    op.drop_index("ix_enrollment_slots_enrollment_id", table_name="enrollment_slots")
    op.drop_index(op.f("ix_enrollment_slots_id"), table_name="enrollment_slots")
    op.drop_table("enrollment_slots")

    op.execute("DELETE FROM enrollments")

    op.add_column("enrollments", sa.Column("clase_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "enrollments_clase_id_fkey",
        "enrollments",
        "clases",
        ["clase_id"],
        ["id"],
    )

    op.drop_constraint("fk_enrollments_turno_id", "enrollments", type_="foreignkey")
    op.drop_column("enrollments", "amount")
    op.drop_column("enrollments", "enrollment_type")
    op.drop_column("enrollments", "turno_id")

    op.execute("DROP TYPE IF EXISTS enrollment_type_enum")
