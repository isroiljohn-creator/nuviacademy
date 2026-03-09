"""Merge Yashabot and Nuvi headers

Revision ID: adff80fdda36
Revises: 6b2e02e7c0fa, fe1234567890
Create Date: 2026-03-09 04:30:51.465196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adff80fdda36'
down_revision: Union[str, None] = ('6b2e02e7c0fa', 'fe1234567890')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
