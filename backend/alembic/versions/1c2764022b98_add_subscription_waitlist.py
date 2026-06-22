"""feat: agregar tabla subscription_waitlist para lista de espera de abonos

Revision ID: 1c2764022b98
Revises: c3d4e5f6a7b8
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "1c2764022b98"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DO...EXCEPTION tolera el caso en que el tipo ya exista (DB sucia por migración
    # anterior fallida), sin afectar una instalación limpia.
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE waitlist_status_enum AS ENUM ('waiting', 'promoted', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END
        $$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS subscription_waitlist (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
            turno_id    INTEGER NOT NULL REFERENCES turnos(id) ON DELETE CASCADE,
            status      waitlist_status_enum NOT NULL,
            joined_at   TIMESTAMPTZ NOT NULL,
            promoted_at TIMESTAMPTZ,
            cancelled_at TIMESTAMPTZ,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.create_index("ix_subscription_waitlist_id",           "subscription_waitlist", ["id"])
    op.create_index("ix_subscription_waitlist_turno_status", "subscription_waitlist", ["turno_id", "status"])
    op.create_index("ix_subscription_waitlist_user",         "subscription_waitlist", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_subscription_waitlist_user",         table_name="subscription_waitlist")
    op.drop_index("ix_subscription_waitlist_turno_status", table_name="subscription_waitlist")
    op.drop_index("ix_subscription_waitlist_id",           table_name="subscription_waitlist")
    op.drop_table("subscription_waitlist")
    op.execute("DROP TYPE IF EXISTS waitlist_status_enum")
