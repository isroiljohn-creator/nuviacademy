"""add_workout_streak_to_users

Revision ID: aed3f63d0664
Revises: 24efacce2e8f
Create Date: 2025-12-27 14:57:50.435935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aed3f63d0664'
down_revision: Union[str, None] = '24efacce2e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('streak_workout', sa.Integer(), server_default='0', nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'streak_workout')
