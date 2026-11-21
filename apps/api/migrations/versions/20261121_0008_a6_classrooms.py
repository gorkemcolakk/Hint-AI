"""A6: öğretmen sınıfları ve ebeveyn onaylı kayıtlar

Revision ID: 20261121_0008
Revises: 20261121_0007
Create Date: 2026-11-21

"""

import sqlalchemy as sa
from alembic import op

revision = "20261121_0008"
down_revision = "20261121_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "teacher_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("grade", sa.SmallInteger(), nullable=True),
        sa.Column("join_code", sa.String(12), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_classrooms_teacher_id", "classrooms", ["teacher_id"])

    op.create_table(
        "enrollments",
        sa.Column(
            "classroom_id",
            sa.Uuid(),
            sa.ForeignKey("classrooms.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "child_id",
            sa.Uuid(),
            sa.ForeignKey("child_profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("guardian_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "approved_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_enrollments_child_id", "enrollments", ["child_id"])


def downgrade() -> None:
    op.drop_table("enrollments")
    op.drop_table("classrooms")
