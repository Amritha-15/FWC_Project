"""Add ai_feedback and answers to interview_results

Revision ID: 0003_add_ai_feedback_and_answers
Revises: 0002_add_audit_logs
Create Date: 2026-06-03 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_ai_feedback_and_answers'
down_revision = '0002_add_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable text column for AI feedback and JSON column for structured answers
    op.add_column('interview_results', sa.Column('ai_feedback', sa.Text(), nullable=True))
    op.add_column('interview_results', sa.Column('answers', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('interview_results', 'answers')
    op.drop_column('interview_results', 'ai_feedback')
