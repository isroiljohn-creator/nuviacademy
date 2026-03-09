"""fix_ai_usage_log_user_id_to_bigint

Revision ID: 24efacce2e8f
Revises: fd96a85a4956
Create Date: 2025-12-27 14:37:00.601396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24efacce2e8f'
down_revision: Union[str, None] = 'fd96a85a4956'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('ai_usage_logs', 'user_id',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('ai_usage_logs', 'user_id',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=True)
