"""add missing nuvi columns

Revision ID: fe1234567890
Revises: fd96a85a4956
Create Date: 2026-03-09 04:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'fe1234567890'
down_revision = 'fd96a85a4956'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'is_active' not in columns:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    
    if 'username' not in columns:
        op.add_column('users', sa.Column('username', sa.String(length=255), nullable=True))

    if 'lead_magnet_opened' not in columns:
        op.add_column('users', sa.Column('lead_magnet_opened', sa.Boolean(), server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'lead_magnet_opened')
    op.drop_column('users', 'username')
    op.drop_column('users', 'is_active')
