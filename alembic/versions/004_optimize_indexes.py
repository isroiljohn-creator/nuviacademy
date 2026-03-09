"""Optimize indexes for maximum speed

Revision ID: 004_optimize_indexes
Revises: 003_add_missing_cols
Create Date: 2025-12-15 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_optimize_indexes'
down_revision: Union[str, None] = '003_add_missing_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy.engine.reflection import Inspector
    inspector = Inspector.from_engine(conn)
    cols = [c['name'] for c in inspector.get_columns('users')]
    
    idx1 = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'idx_daily_logs_user_date'")).scalar()
    if not idx1:
        try:
            op.create_index('idx_daily_logs_user_date', 'daily_logs', ['user_id', 'date'], unique=False)
        except Exception:
            pass
            
    idx2 = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'idx_users_active_points'")).scalar()
    if not idx2 and 'active' in cols and 'points' in cols:
        op.create_index('idx_users_active_points', 'users', ['active', 'points'], unique=False)

def downgrade() -> None:
    conn = op.get_bind()
    idx1 = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'idx_daily_logs_user_date'")).scalar()
    if idx1:
        op.drop_index('idx_daily_logs_user_date', table_name='daily_logs')
        
    idx2 = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'idx_users_active_points'")).scalar()
    if idx2:
        op.drop_index('idx_users_active_points', table_name='users')
