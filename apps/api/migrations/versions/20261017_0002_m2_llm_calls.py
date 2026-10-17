"""M2: llm_calls tablosu

Revision ID: 20261017_0002
Revises: 20261016_0001
Create Date: 2026-10-17

"""

import sqlalchemy as sa
from alembic import op

revision = "20261017_0002"
down_revision = "20261016_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_calls",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=False, server_default="v1"),
        sa.Column("token_in", sa.Integer(), nullable=True),
        sa.Column("token_out", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "child_id",
            sa.Uuid(),
            sa.ForeignKey("child_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_llm_calls_created_at", "llm_calls", ["created_at"])
    op.create_index("ix_llm_calls_purpose", "llm_calls", ["purpose"])
    op.create_index("ix_llm_calls_status", "llm_calls", ["status"])
    op.create_index("ix_llm_calls_child_id", "llm_calls", ["child_id"])


def downgrade() -> None:
    op.drop_index("ix_llm_calls_child_id", table_name="llm_calls")
    op.drop_index("ix_llm_calls_status", table_name="llm_calls")
    op.drop_index("ix_llm_calls_purpose", table_name="llm_calls")
    op.drop_index("ix_llm_calls_created_at", table_name="llm_calls")
    op.drop_table("llm_calls")
