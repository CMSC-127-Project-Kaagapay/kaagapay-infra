"""add ticket purge logs

Revision ID: c3f9a2e8d417
Revises: 9a1c7e4b2d10
Create Date: 2026-11-05 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f9a2e8d417'
down_revision: Union[str, Sequence[str], None] = '9a1c7e4b2d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ticket_purge_logs',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('public_case_id', sa.String(length=20), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('purged_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ticket_purge_logs_public_case_id', 'ticket_purge_logs', ['public_case_id'])
    # Admin-only table: RLS on with no policies, so the public Data API cannot read it.
    op.execute('ALTER TABLE ticket_purge_logs ENABLE ROW LEVEL SECURITY')
    # The purge worker looks for tickets deleted before a cutoff; only deleted rows are in this index.
    op.create_index(
        'ix_incident_tickets_deleted_at', 'incident_tickets', ['deleted_at'],
        postgresql_where=sa.text('deleted_at IS NOT NULL'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_incident_tickets_deleted_at', table_name='incident_tickets')
    op.drop_index('ix_ticket_purge_logs_public_case_id', table_name='ticket_purge_logs')
    op.drop_table('ticket_purge_logs')
