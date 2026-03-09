"""Atomic limits

Revision ID: 002_atomic_limits
Revises: 001_initial
Create Date: 2025-12-15 20:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_atomic_limits'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('chat_last_use_date', sa.String(), nullable=True))
    op.add_column('users', sa.Column('chat_daily_uses', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'chat_daily_uses')
    op.drop_column('users', 'chat_last_use_date')
