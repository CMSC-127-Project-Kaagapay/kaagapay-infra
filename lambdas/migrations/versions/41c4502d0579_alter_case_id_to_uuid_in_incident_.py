"""ALTER case_id to uuid in incident_tickets : MATCH ERD

Revision ID: 41c4502d0579
Revises:
Create Date: 2026-04-26 14:53:48.487506

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "41c4502d0579"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Create the new admins table
    op.create_table(
        "admins",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # 2. DROP the foreign key constraints pointing to incident_tickets
    op.drop_constraint(
        "notifications_ticket_id_fkey", "notifications", type_="foreignkey"
    )
    # Note: Alembic standard naming convention assumed here for the status logs table
    op.drop_constraint(
        "ticket_status_logs_ticket_id_fkey", "ticket_status_logs", type_="foreignkey"
    )

    # 3. ALTER ALL the columns to UUID (with explicit USING casts for Postgres)
    op.alter_column(
        "incident_tickets",
        "case_id",
        existing_type=sa.VARCHAR(length=16),
        type_=sa.Uuid(),
        postgresql_using="case_id::uuid",
        existing_nullable=False,
    )
    op.alter_column(
        "notifications",
        "ticket_id",
        existing_type=sa.VARCHAR(length=16),
        type_=sa.Uuid(),
        postgresql_using="ticket_id::uuid",
        existing_nullable=False,
    )
    op.alter_column(
        "ticket_status_logs",
        "ticket_id",
        existing_type=sa.VARCHAR(length=16),
        type_=sa.Uuid(),
        postgresql_using="ticket_id::uuid",
        existing_nullable=False,
    )

    # 4. RECREATE the foreign key constraints
    op.create_foreign_key(
        "notifications_ticket_id_fkey",
        "notifications",
        "incident_tickets",
        ["ticket_id"],
        ["case_id"],
    )
    op.create_foreign_key(
        "ticket_status_logs_ticket_id_fkey",
        "ticket_status_logs",
        "incident_tickets",
        ["ticket_id"],
        ["case_id"],
    )

    # 5. Handle the volunteer_applications changes
    # Added server_default="Unknown" to prevent the NotNullViolation
    op.add_column(
        "volunteer_applications",
        sa.Column(
            "first_name",
            sa.String(length=100),
            server_default="Unknown",
            nullable=False,
        ),
    )
    op.add_column(
        "volunteer_applications",
        sa.Column(
            "last_name", sa.String(length=100), server_default="Unknown", nullable=False
        ),
    )
    op.add_column(
        "volunteer_applications", sa.Column("reviewed_by", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "volunteer_applications_reviewed_by_fkey",
        "volunteer_applications",
        "admins",
        ["reviewed_by"],
        ["id"],
    )
    op.drop_column("volunteer_applications", "full_name")


def downgrade() -> None:
    """Downgrade schema."""

    # 1. Revert volunteer_applications changes
    op.add_column(
        "volunteer_applications",
        sa.Column(
            "full_name", sa.VARCHAR(length=100), autoincrement=False, nullable=False
        ),
    )
    op.drop_constraint(
        "volunteer_applications_reviewed_by_fkey",
        "volunteer_applications",
        type_="foreignkey",
    )
    op.drop_column("volunteer_applications", "reviewed_by")
    op.drop_column("volunteer_applications", "last_name")
    op.drop_column("volunteer_applications", "first_name")

    # 2. DROP foreign keys before reverting types
    op.drop_constraint(
        "notifications_ticket_id_fkey", "notifications", type_="foreignkey"
    )
    op.drop_constraint(
        "ticket_status_logs_ticket_id_fkey", "ticket_status_logs", type_="foreignkey"
    )

    # 3. Revert types back to VARCHAR
    op.alter_column(
        "ticket_status_logs",
        "ticket_id",
        existing_type=sa.Uuid(),
        type_=sa.VARCHAR(length=16),
        existing_nullable=False,
    )
    op.alter_column(
        "notifications",
        "ticket_id",
        existing_type=sa.Uuid(),
        type_=sa.VARCHAR(length=16),
        existing_nullable=False,
    )
    op.alter_column(
        "incident_tickets",
        "case_id",
        existing_type=sa.Uuid(),
        type_=sa.VARCHAR(length=16),
        existing_nullable=False,
    )

    # 4. Re-link foreign keys on the VARCHAR columns
    op.create_foreign_key(
        "notifications_ticket_id_fkey",
        "notifications",
        "incident_tickets",
        ["ticket_id"],
        ["case_id"],
    )
    op.create_foreign_key(
        "ticket_status_logs_ticket_id_fkey",
        "ticket_status_logs",
        "incident_tickets",
        ["ticket_id"],
        ["case_id"],
    )

    # 5. Drop admins table
    op.drop_table("admins")
