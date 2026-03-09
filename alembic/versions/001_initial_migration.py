"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-15 20:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotency Check
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. Users
    if 'users' not in tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('telegram_id', sa.BigInteger(), nullable=True),
            sa.Column('username', sa.String(), nullable=True),
            sa.Column('full_name', sa.String(), nullable=True),
            sa.Column('phone', sa.String(), nullable=True),
            sa.Column('age', sa.Integer(), nullable=True),
            sa.Column('gender', sa.String(), nullable=True),
            sa.Column('height', sa.Integer(), nullable=True),
            sa.Column('weight', sa.Float(), nullable=True),
            sa.Column('target_weight', sa.Float(), nullable=True),
            sa.Column('goal', sa.String(), nullable=True),
            sa.Column('activity_level', sa.String(), nullable=True),
            sa.Column('allergies', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('is_premium', sa.Boolean(), nullable=True),
            sa.Column('premium_until', sa.DateTime(), nullable=True),
            sa.Column('points', sa.Integer(), nullable=True),
            sa.Column('referral_code', sa.String(), nullable=True),
            sa.Column('referrer_id', sa.Integer(), nullable=True),
            sa.Column('last_checkin', sa.String(), nullable=True),
            sa.Column('active', sa.Boolean(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('yasha_points', sa.Integer(), nullable=True),
            sa.Column('streak_water', sa.Integer(), nullable=True),
            sa.Column('streak_sleep', sa.Integer(), nullable=True),
            sa.Column('streak_mood', sa.Integer(), nullable=True),
            sa.Column('calorie_last_use_date', sa.String(), nullable=True),
            sa.Column('calorie_daily_uses', sa.Integer(), nullable=True),
            sa.Column('ai_menu_count', sa.Integer(), nullable=True),
            sa.Column('ai_workout_count', sa.Integer(), nullable=True),
            sa.Column('ai_last_reset_month', sa.String(), nullable=True),
            sa.Column('plan_type', sa.String(), nullable=True),
            sa.Column('daily_stats', sa.Text(), nullable=True),
            sa.Column('trial_start', sa.String(), nullable=True),
            sa.Column('trial_used', sa.Integer(), nullable=True),
            sa.Column('auto_renew', sa.Integer(), nullable=True),
            sa.Column('onboarding_state', sa.Integer(), nullable=True),
            sa.Column('onboarding_data', sa.Text(), nullable=True),
            sa.Column('utm_raw', sa.String(), nullable=True),
            sa.Column('utm_source', sa.String(), nullable=True),
            sa.Column('utm_campaign', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)
        op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
        op.create_foreign_key('fk_users_referrer', 'users', 'users', ['referrer_id'], ['id'])

    # 2. Daily Logs
    if 'daily_logs' not in tables:
        op.create_table('daily_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('date', sa.String(), nullable=True),
            sa.Column('water_drank', sa.Boolean(), nullable=True),
            sa.Column('workout_done', sa.Boolean(), nullable=True),
            sa.Column('steps_count', sa.Integer(), nullable=True),
            sa.Column('steps', sa.Integer(), nullable=True),
            sa.Column('calories_consumed', sa.Integer(), nullable=True),
            sa.Column('stages_reward_claimed', sa.Boolean(), nullable=True),
            sa.Column('steps_reward_claimed', sa.Boolean(), nullable=True),
            sa.Column('water_ml', sa.Integer(), nullable=True),
            sa.Column('sleep_hours', sa.Float(), nullable=True),
            sa.Column('mood', sa.String(), nullable=True),
            sa.Column('mood_reason', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_daily_logs_date'), 'daily_logs', ['date'], unique=False)
        op.create_index(op.f('ix_daily_logs_id'), 'daily_logs', ['id'], unique=False)

    # 3. Plans
    if 'plans' not in tables:
        op.create_table('plans',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('type', sa.String(), nullable=True),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)

    # 4. Transactions
    if 'transactions' not in tables:
        op.create_table('transactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(), nullable=True),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)

    # 5. Feedback
    if 'feedback' not in tables:
        op.create_table('feedback',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)

    # 6. Orders
    if 'orders' not in tables:
        op.create_table('orders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.String(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('days', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
        op.create_index(op.f('ix_orders_order_id'), 'orders', ['order_id'], unique=True)

    # 7. Activity Logs
    if 'activity_logs' not in tables:
        op.create_table('activity_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('type', sa.String(), nullable=True),
            sa.Column('payload', sa.Text(), nullable=True),
            sa.Column('ts', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_activity_logs_id'), 'activity_logs', ['id'], unique=False)

    # 8. Calorie Logs
    if 'calorie_logs' not in tables:
        op.create_table('calorie_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('total_kcal', sa.Integer(), nullable=True),
            sa.Column('json_data', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_calorie_logs_id'), 'calorie_logs', ['id'], unique=False)

    # 9. Menu Templates
    if 'menu_templates' not in tables:
        op.create_table('menu_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('profile_key', sa.String(), nullable=True),
            sa.Column('menu_json', sa.Text(), nullable=True),
            sa.Column('shopping_list_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_menu_templates_id'), 'menu_templates', ['id'], unique=False)
        op.create_index(op.f('ix_menu_templates_profile_key'), 'menu_templates', ['profile_key'], unique=True)

    # 10. User Menu Links
    if 'user_menu_links' not in tables:
        op.create_table('user_menu_links',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('menu_template_id', sa.Integer(), nullable=True),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('current_day_index', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['menu_template_id'], ['menu_templates.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_menu_links_id'), 'user_menu_links', ['id'], unique=False)

    # 11. Workout Templates
    if 'workout_templates' not in tables:
        op.create_table('workout_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('profile_key', sa.String(), nullable=True),
            sa.Column('workout_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workout_templates_id'), 'workout_templates', ['id'], unique=False)
        op.create_index(op.f('ix_workout_templates_profile_key'), 'workout_templates', ['profile_key'], unique=True)

    # 12. User Workout Links
    if 'user_workout_links' not in tables:
        op.create_table('user_workout_links',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('workout_template_id', sa.Integer(), nullable=True),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('current_day_index', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['workout_template_id'], ['workout_templates.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_workout_links_id'), 'user_workout_links', ['id'], unique=False)

    # 13. Workout Cache
    if 'workout_cache' not in tables:
        op.create_table('workout_cache',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('plan_text', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workout_cache_id'), 'workout_cache', ['id'], unique=False)

    # 14. Menu Cache
    if 'menu_cache' not in tables:
        op.create_table('menu_cache',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('menu_text', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_menu_cache_id'), 'menu_cache', ['id'], unique=False)

    # 15. Admin Logs
    if 'admin_logs' not in tables:
        op.create_table('admin_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('admin_id', sa.BigInteger(), nullable=True),
            sa.Column('action', sa.String(), nullable=True),
            sa.Column('target_id', sa.BigInteger(), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_admin_logs_id'), 'admin_logs', ['id'], unique=False)

    # 16. Bot Content
    if 'bot_content' not in tables:
        op.create_table('bot_content',
            sa.Column('key', sa.String(), nullable=False),
            sa.Column('value', sa.Text(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('key')
        )

def downgrade() -> None:
    # Reverse order
    op.drop_table('bot_content')
    op.drop_index(op.f('ix_admin_logs_id'), table_name='admin_logs')
    op.drop_table('admin_logs')
    op.drop_index(op.f('ix_menu_cache_id'), table_name='menu_cache')
    op.drop_table('menu_cache')
    op.drop_index(op.f('ix_workout_cache_id'), table_name='workout_cache')
    op.drop_table('workout_cache')
    op.drop_index(op.f('ix_user_workout_links_id'), table_name='user_workout_links')
    op.drop_table('user_workout_links')
    op.drop_index(op.f('ix_workout_templates_profile_key'), table_name='workout_templates')
    op.drop_index(op.f('ix_workout_templates_id'), table_name='workout_templates')
    op.drop_table('workout_templates')
    op.drop_index(op.f('ix_user_menu_links_id'), table_name='user_menu_links')
    op.drop_table('user_menu_links')
    op.drop_index(op.f('ix_menu_templates_profile_key'), table_name='menu_templates')
    op.drop_index(op.f('ix_menu_templates_id'), table_name='menu_templates')
    op.drop_table('menu_templates')
    op.drop_index(op.f('ix_calorie_logs_id'), table_name='calorie_logs')
    op.drop_table('calorie_logs')
    op.drop_index(op.f('ix_activity_logs_id'), table_name='activity_logs')
    op.drop_table('activity_logs')
    op.drop_index(op.f('ix_orders_order_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_table('feedback')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_plans_id'), table_name='plans')
    op.drop_table('plans')
    op.drop_index(op.f('ix_daily_logs_id'), table_name='daily_logs')
    op.drop_index(op.f('ix_daily_logs_date'), table_name='daily_logs')
    op.drop_table('daily_logs')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
