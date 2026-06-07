"""Add audit_logs table

Revision ID: 0002_add_audit_logs
Revises: 0001_initial_schema
Create Date: 2026-06-03 00:00:00.000001
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_audit_logs'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=200), nullable=False),
        sa.Column('target_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
