"""Add is_onboarded column to User

Revision ID: 007_add_is_onboarded
Revises: 04e2cafb962d
Create Date: 2025-12-25 11:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_add_is_onboarded'
down_revision: Union[str, None] = '04e2cafb962d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add column as nullable first
    op.add_column('users', sa.Column('is_onboarded', sa.Boolean(), nullable=True))
    
    # Set TRUE for users who already have core data, others FALSE
    op.execute("UPDATE users SET is_onboarded = TRUE WHERE age IS NOT NULL AND weight IS NOT NULL")
    op.execute("UPDATE users SET is_onboarded = FALSE WHERE is_onboarded IS NULL")
    
    # Make it non-nullable with server default
    op.alter_column('users', 'is_onboarded',
               existing_type=sa.Boolean(),
               nullable=False,
               server_default=sa.text('false'))

def downgrade() -> None:
    op.drop_column('users', 'is_onboarded')
