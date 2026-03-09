"""add_elixir_column_to_users

Revision ID: c04bbd5ec056
Revises: e123456789ab
Create Date: 2025-12-28 14:42:37.019223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c04bbd5ec056'
down_revision: Union[str, None] = 'e123456789ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('elixir', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'elixir')
