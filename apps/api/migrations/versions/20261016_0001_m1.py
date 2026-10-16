"""M1: kimlik, rıza ve çocuk profili tabloları

Revision ID: 20261016_0001
Revises:
Create Date: 2026-10-16

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261016_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("locale", sa.String(10), nullable=False, server_default="tr-TR"),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "role IN ('guardian','teacher','admin','moderator')", name="ck_users_role"
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "child_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "guardian_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nickname", sa.String(100), nullable=False),
        sa.Column("birth_year", sa.SmallInteger(), nullable=False),
        sa.Column("grade", sa.SmallInteger(), nullable=False),
        sa.Column("age_band", sa.String(10), nullable=False),
        sa.Column("daily_new_problem_limit", sa.SmallInteger(), nullable=False, server_default="5"),
        sa.Column(
            "solution_policy",
            sa.String(40),
            nullable=False,
            server_default="after_attempts_with_notice",
        ),
        sa.Column("privacy_level", sa.String(20), nullable=False, server_default="summary_only"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "age_band IN ('7-10','11-13','14-17')", name="ck_child_profiles_age_band"
        ),
        sa.CheckConstraint(
            "solution_policy IN ('never','after_attempts_with_notice','guardian_only',"
            "'similar_example_only')",
            name="ck_child_profiles_solution_policy",
        ),
        sa.CheckConstraint(
            "privacy_level IN ('summary_only','full_transcript')",
            name="ck_child_profiles_privacy_level",
        ),
    )
    op.create_index("ix_child_profiles_guardian_id", "child_profiles", ["guardian_id"])

    op.create_table(
        "consents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "child_id",
            sa.Uuid(),
            sa.ForeignKey("child_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "guardian_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('service','analytics','llm_processing','photo_processing')",
            name="ck_consents_purpose",
        ),
    )
    op.create_index("ix_consents_child_id", "consents", ["child_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "pairing_codes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "child_id",
            sa.Uuid(),
            sa.ForeignKey("child_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.SmallInteger(), nullable=False, server_default="5"),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("code_hash", name="uq_pairing_codes_code_hash"),
    )
    op.create_index("ix_pairing_codes_child_id", "pairing_codes", ["child_id"])
    op.create_index("ix_pairing_codes_code_hash", "pairing_codes", ["code_hash"])


def downgrade() -> None:
    op.drop_table("pairing_codes")
    op.drop_table("refresh_tokens")
    op.drop_table("consents")
    op.drop_table("child_profiles")
    op.drop_table("users")
