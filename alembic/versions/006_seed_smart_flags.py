
"""seed_smart_flags

Revision ID: 006_seed_smart_flags
Revises: 005_add_observability
Create Date: 2025-12-15 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Boolean, Integer, Text

# revision identifiers, used by Alembic.
revision = '006_seed_smart_flags'
down_revision = '005_add_observability'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Define table interface for bulk insert
    feature_flags = table('feature_flags',
        column('key', String),
        column('enabled', Boolean),
        column('rollout_percent', Integer),
        column('allowlist', Text),
        column('denylist', Text)
    )

    # 2. Seed New Flags (Default OFF)
    # stateful_ai_context: Inject user stat summary into prompts
    # progress_insights: Show motivation stats
    # retention_engine: Send inactivity nudges
    # smart_paywall: Behavioral Monetization
    # founder_tone: Special persona
    
    op.bulk_insert(feature_flags, [
        {
            'key': 'stateful_ai_context',
            'enabled': False,
            'rollout_percent': 0,
            'allowlist': '[]',
            'denylist': '[]'
        },
        {
            'key': 'progress_insights',
            'enabled': False,
            'rollout_percent': 0,
            'allowlist': '[]',
            'denylist': '[]'
        },
        {
            'key': 'retention_engine',
            'enabled': False,
            'rollout_percent': 0,
            'allowlist': '[]',
            'denylist': '[]'
        },
        {
            'key': 'smart_paywall',
            'enabled': False,
            'rollout_percent': 0,
            'allowlist': '[]',
            'denylist': '[]'
        },
        {
            'key': 'founder_tone',
            'enabled': False,
            'rollout_percent': 0,
            'allowlist': '[]',
            'denylist': '[]'
        }
    ])

def downgrade() -> None:
    # Remove seeded flags
    op.execute("DELETE FROM feature_flags WHERE key IN ('stateful_ai_context', 'progress_insights', 'retention_engine', 'smart_paywall', 'founder_tone')")
