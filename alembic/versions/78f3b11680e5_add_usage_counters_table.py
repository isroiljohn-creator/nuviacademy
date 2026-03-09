"""add_usage_counters_table

Revision ID: 78f3b11680e5
Revises: 
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78f3b11680e5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create usage_counters table
    op.create_table(
        'usage_counters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('feature_key', sa.String(length=50), nullable=False),
        sa.Column('period_type', sa.String(length=10), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('used_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'feature_key', 'period_type', 'period_start', name='unique_usage')
    )
    
    # Create index for faster lookups
    op.create_index('idx_usage_lookup', 'usage_counters', ['user_id', 'feature_key', 'period_start'])


def downgrade():
    op.drop_index('idx_usage_lookup', table_name='usage_counters')
    op.drop_table('usage_counters')
