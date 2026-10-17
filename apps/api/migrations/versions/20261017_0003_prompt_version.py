"""M2: llm_calls tablosunda prompt_version alanı ve indeksi

Revision ID: 20261017_0003
Revises: 20261017_0002
Create Date: 2026-10-17

"""

import sqlalchemy as sa
from alembic import op

revision = "20261017_0003"
down_revision = "20261017_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("llm_calls")]
    if "prompt_version" not in columns:
        op.add_column(
            "llm_calls",
            sa.Column("prompt_version", sa.String(50), nullable=False, server_default="v1"),
        )

    indexes = [i["name"] for i in inspector.get_indexes("llm_calls")]
    if "ix_llm_calls_prompt_version" not in indexes:
        op.create_index("ix_llm_calls_prompt_version", "llm_calls", ["prompt_version"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [i["name"] for i in inspector.get_indexes("llm_calls")]
    if "ix_llm_calls_prompt_version" in indexes:
        op.drop_index("ix_llm_calls_prompt_version", table_name="llm_calls")
