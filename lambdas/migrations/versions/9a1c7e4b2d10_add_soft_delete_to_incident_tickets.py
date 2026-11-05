"""add soft delete to incident tickets

Revision ID: 9a1c7e4b2d10
Revises: 23d502956066
Create Date: 2026-11-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1c7e4b2d10'
down_revision: Union[str, Sequence[str], None] = '23d502956066'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('incident_tickets', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('incident_tickets', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    op.add_column('incident_tickets', sa.Column('deleted_reason', sa.String(length=255), nullable=True))
    op.create_foreign_key(
        'fk_incident_tickets_deleted_by_admins',
        'incident_tickets', 'admins', ['deleted_by'], ['id'], ondelete='SET NULL',
    )
    # Partial index: the dashboard only ever lists live tickets, newest first.
    op.create_index(
        'ix_incident_tickets_live_status_created',
        'incident_tickets', ['status', sa.text('created_at DESC'), sa.text('id DESC')],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_incident_tickets_live_status_created', table_name='incident_tickets')
    op.drop_constraint('fk_incident_tickets_deleted_by_admins', 'incident_tickets', type_='foreignkey')
    op.drop_column('incident_tickets', 'deleted_reason')
    op.drop_column('incident_tickets', 'deleted_by')
    op.drop_column('incident_tickets', 'deleted_at')
