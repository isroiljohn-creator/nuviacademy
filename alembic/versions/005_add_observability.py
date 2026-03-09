"""Add Observability Tables

Revision ID: 005_add_observability
Revises: 004_optimize_indexes
Create Date: 2025-12-15 23:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_observability'
down_revision: Union[str, None] = '004_optimize_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Feature Flags
    op.create_table(
        'feature_flags',
        sa.Column('key', sa.String(), primary_key=True),
        sa.Column('enabled', sa.Boolean(), default=False),
        sa.Column('rollout_percent', sa.Integer(), default=0),
        sa.Column('allowlist', sa.Text(), default="[]"),
        sa.Column('denylist', sa.Text(), default="[]"),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 2. Admin Events
    op.create_table(
        'admin_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('meta', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Indexes
    op.create_index('idx_admin_events_created_at', 'admin_events', ['created_at'])
    op.create_index('idx_admin_events_type_created', 'admin_events', ['event_type', 'created_at'])
    op.create_index('idx_admin_events_user_created', 'admin_events', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('admin_events')
    op.drop_table('feature_flags')
