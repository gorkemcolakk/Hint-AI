"""M3: problems ve hidden_solutions tabloları

Revision ID: 20261116_0005
Revises: 20261116_0004
Create Date: 2026-11-16

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261116_0005"
down_revision = "20261116_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hidden_solutions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("problem_hash", sa.String(64), nullable=False),
        sa.Column("grade", sa.SmallInteger(), nullable=True),
        sa.Column("topic", sa.String(120), nullable=True),
        sa.Column("steps", postgresql.JSONB(), nullable=False),
        sa.Column("final_answer", sa.Text(), nullable=False),
        sa.Column("sympy_check", postgresql.JSONB(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_hidden_solutions_problem_hash", "hidden_solutions", ["problem_hash"])

    op.create_table(
        "problems",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "child_id",
            sa.Uuid(),
            sa.ForeignKey("child_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("masked_text", sa.Text(), nullable=False),
        sa.Column("problem_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "solution_id",
            sa.Uuid(),
            sa.ForeignKey("hidden_solutions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('verified','low_confidence','unverifiable','failed')",
            name="ck_problems_status",
        ),
    )
    op.create_index("ix_problems_child_id", "problems", ["child_id"])
    op.create_index("ix_problems_problem_hash", "problems", ["problem_hash"])


def downgrade() -> None:
    op.drop_table("problems")
    op.drop_table("hidden_solutions")
