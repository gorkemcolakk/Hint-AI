"""A3: moderation_events (güvenlik olayları; çocuk metni saklanmaz)

Revision ID: 20261121_0007
Revises: 20261121_0006
Create Date: 2026-11-21

"""

import sqlalchemy as sa
from alembic import op

revision = "20261121_0007"
down_revision = "20261121_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "moderation_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "child_id",
            sa.Uuid(),
            sa.ForeignKey("child_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "problem_id",
            sa.Uuid(),
            sa.ForeignKey("problems.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("stage", sa.String(10), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("notify_guardian", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("stage IN ('input','output')", name="ck_moderation_stage"),
    )
    op.create_index("ix_moderation_events_child_id", "moderation_events", ["child_id"])
    op.create_index("ix_moderation_events_category", "moderation_events", ["category"])


def downgrade() -> None:
    op.drop_table("moderation_events")
