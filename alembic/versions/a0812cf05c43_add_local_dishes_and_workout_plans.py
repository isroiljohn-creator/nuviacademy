"""add_local_dishes_and_workout_plans

Revision ID: a0812cf05c43
Revises: 007_add_is_onboarded
Create Date: 2025-12-27 13:29:09.452927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0812cf05c43'
down_revision: Union[str, None] = '007_add_is_onboarded'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check existing tables to avoid DuplicateTable error
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # 1. local_dishes
    if 'local_dishes' not in existing_tables:
        op.create_table(
            'local_dishes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name_uz', sa.String(), nullable=False),
            sa.Column('meal_type', sa.String(), nullable=False),
            sa.Column('portion_type', sa.String(), nullable=False),
            sa.Column('total_kcal', sa.Integer(), nullable=False),
            sa.Column('protein_g', sa.Float(), nullable=False),
            sa.Column('fat_g', sa.Float(), nullable=False),
            sa.Column('carbs_g', sa.Float(), nullable=False),
            sa.Column('goal_tag', sa.String(), nullable=False),
            sa.Column('variant', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name_uz', 'portion_type', 'variant', name='uq_local_dishes_name_portion_variant')
        )
        op.create_index('ix_local_dishes_goal_meal_variant_active', 'local_dishes', ['goal_tag', 'meal_type', 'variant', 'is_active'])

    # 2. local_dish_ingredients
    if 'local_dish_ingredients' not in existing_tables:
        op.create_table(
            'local_dish_ingredients',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('dish_id', sa.Integer(), nullable=False),
            sa.Column('ingredient_name_uz', sa.String(), nullable=False),
            sa.Column('grams', sa.Integer(), nullable=False),
            sa.Column('fdc_id', sa.BigInteger(), nullable=True),
            sa.ForeignKeyConstraint(['dish_id'], ['local_dishes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_local_dish_ingredients_dish_id'), 'local_dish_ingredients', ['dish_id'])

    # 3. workout_plans
    if 'workout_plans' not in existing_tables:
        op.create_table(
            'workout_plans',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('goal_tag', sa.String(), nullable=False),
            sa.Column('level', sa.String(), nullable=False),
            sa.Column('place', sa.String(), nullable=False),
            sa.Column('days_json', sa.JSON(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_workout_plans_goal_level_place_active', 'workout_plans', ['goal_tag', 'level', 'place', 'is_active'])

    # 4. exercises modification
    op.add_column('exercises', sa.Column('muscle_group', sa.String(), nullable=True))
    op.add_column('exercises', sa.Column('level', sa.String(), nullable=True))
    op.add_column('exercises', sa.Column('place', sa.String(), nullable=True))
    op.add_column('exercises', sa.Column('duration_sec', sa.Integer(), nullable=True))
    # video_url already exists in some definitions? Let's check models.py again.
    # From viewed files: video_url is in models.py line 324. 
    # Let me check if it's already in the DB from psql output earlier.
    # The psql output for \d exercises showed video_url exists.
    # op.add_column('exercises', sa.Column('video_url', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('exercises', 'duration_sec')
    op.drop_column('exercises', 'place')
    op.drop_column('exercises', 'level')
    op.drop_column('exercises', 'muscle_group')
    op.drop_table('workout_plans')
    op.drop_table('local_dish_ingredients')
    op.drop_table('local_dishes')
