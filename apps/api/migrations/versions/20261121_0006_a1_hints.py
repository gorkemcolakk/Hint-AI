"""A1: ipucu merdiveni — hints, attempts ve problems öğretim durumu

Revision ID: 20261121_0006
Revises: 20261116_0005
Create Date: 2026-11-21

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261121_0006"
down_revision = "20261116_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "problems", sa.Column("state", sa.String(20), nullable=False, server_default="open")
    )
    op.add_column("problems", sa.Column("current_hint_level", sa.SmallInteger(), nullable=True))
    op.add_column("problems", sa.Column("solved_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint("ck_problems_state", "problems", "state IN ('open','solved')")

    op.create_table(
        "hints",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "problem_id",
            sa.Uuid(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("leak_check", postgresql.JSONB(), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("llm_call_id", sa.Uuid(), nullable=True),
        sa.Column("helpful", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("level BETWEEN 0 AND 5", name="ck_hints_level"),
        sa.CheckConstraint("source IN ('llm','fallback')", name="ck_hints_source"),
    )
    op.create_index("ix_hints_problem_id", "hints", ["problem_id"])

    op.create_table(
        "attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "problem_id",
            sa.Uuid(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer_masked", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_attempts_problem_id", "attempts", ["problem_id"])


def downgrade() -> None:
    op.drop_table("attempts")
    op.drop_table("hints")
    op.drop_constraint("ck_problems_state", "problems", type_="check")
    op.drop_column("problems", "solved_at")
    op.drop_column("problems", "current_hint_level")
    op.drop_column("problems", "state")
