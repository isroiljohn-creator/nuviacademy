"""Add stages_reward_claimed to daily_logs

Revision ID: 003_add_missing_cols
Revises: 002_atomic_limits
Create Date: 2025-12-15 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '003_add_missing_cols'
down_revision: Union[str, None] = '002_atomic_limits'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('daily_logs')]

    if 'stages_reward_claimed' not in columns:
        op.add_column('daily_logs', sa.Column('stages_reward_claimed', sa.Boolean(), nullable=True))
    
    if 'steps_reward_claimed' not in columns:
        op.add_column('daily_logs', sa.Column('steps_reward_claimed', sa.Boolean(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('daily_logs')]

    if 'stages_reward_claimed' in columns:
        op.drop_column('daily_logs', 'stages_reward_claimed')
    
    if 'steps_reward_claimed' in columns:
        op.drop_column('daily_logs', 'steps_reward_claimed')
