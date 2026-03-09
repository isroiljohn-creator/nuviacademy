"""upgrade_days_json_to_jsonb

Revision ID: fd96a85a4956
Revises: a0812cf05c43
Create Date: 2025-12-27 14:19:10.296916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd96a85a4956'
down_revision: Union[str, None] = 'a0812cf05c43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Upgrade days_json to JSONB
    op.execute('ALTER TABLE workout_plans ALTER COLUMN days_json TYPE JSONB USING days_json::jsonb')
    
    # 2. Add video_url to exercises if somehow missing (it exists in models, but psql confirmed it exists too)
    # Just in case of different environments.
    
    # 3. Ensure indexing is correct
    # The previous migration already added ix_workout_plans_goal_level_place_active.
    pass


def downgrade() -> None:
    # Downgrade days_json back to JSON
    op.execute('ALTER TABLE workout_plans ALTER COLUMN days_json TYPE JSON USING days_json::json')
    pass
