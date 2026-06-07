"""Initial HRMS schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-06-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("google_id", sa.Text(), nullable=True, unique=True),
        sa.Column("profile_picture", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("department_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("employee_code", sa.String(length=50), nullable=True, unique=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("manager_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("designation", sa.String(length=100), nullable=True),
        sa.Column("salary", sa.Numeric(10, 2), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required_skills", sa.Text(), nullable=True),
        sa.Column("experience_required", sa.String(length=50), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Open"),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
    )

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("experience", sa.Text(), nullable=True),
        sa.Column("resume_url", sa.Text(), nullable=True),
        sa.Column("current_status", sa.String(length=50), nullable=False, server_default="Applied"),
        sa.Column("skills", sa.Text(), nullable=True),
        sa.Column("certifications", sa.Text(), nullable=True),
        sa.Column("projects", sa.Text(), nullable=True),
        sa.Column("resume_parsed_at", sa.DateTime(), nullable=True),
        sa.Column("resume_summary", sa.Text(), nullable=True),
        sa.Column("resume_quality_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("skill_strength_score", sa.Numeric(5, 2), nullable=True),
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("resume_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("interview_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("application_status", sa.String(length=50), nullable=False, server_default="Applied"),
        sa.Column("applied_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ranking_position", sa.Integer(), nullable=True),
        sa.Column("hiring_confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("skill_gap", sa.JSON(), nullable=True),
        sa.Column("hiring_recommendation", sa.JSON(), nullable=True),
    )

    op.create_table(
        "interview_schedules",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=True),
        sa.Column("interview_date", sa.Date(), nullable=False),
        sa.Column("interview_time", sa.Time(), nullable=False),
        sa.Column("meeting_link", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=True),
        sa.Column("check_in", sa.DateTime(), nullable=True),
        sa.Column("check_out", sa.DateTime(), nullable=True),
        sa.Column("work_hours", sa.Numeric(6, 2), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
    )

    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )

    op.create_table(
        "performance_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=True),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )

    op.create_table(
        "kpis",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("team", sa.String(length=100), nullable=False),
        sa.Column("metric", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("kpis")
    op.drop_table("performance_reviews")
    op.drop_table("leave_requests")
    op.drop_table("attendance")
    op.drop_table("interview_schedules")
    op.drop_table("applications")
    op.drop_table("candidates")
    op.drop_table("jobs")
    op.drop_table("employees")
    op.drop_table("departments")
    op.drop_table("users")
