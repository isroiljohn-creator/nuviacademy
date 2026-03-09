"""merge_heads

Revision ID: 197375427b62
Revises: 78f3b11680e5, c2d332e1d44d
Create Date: 2025-12-28 12:37:13.483949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '197375427b62'
down_revision: Union[str, None] = ('78f3b11680e5', 'c2d332e1d44d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
