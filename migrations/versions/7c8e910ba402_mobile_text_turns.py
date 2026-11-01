"""Bounded authenticated text conversation turns, without automatic context writes."""

import sqlalchemy as sa
from alembic import op

revision = "7c8e910ba402"
down_revision = "f735a2ec901b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_text_turns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario_id", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column(
            "response_id",
            sa.String(36),
            sa.ForeignKey("policy_projections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("client_turn_id", sa.String(128), nullable=False),
        sa.Column("session_id", sa.String(36)),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("response_revision", sa.Integer(), nullable=False),
        sa.Column("context_revision", sa.Integer(), nullable=False),
        sa.Column("input_versions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result", sa.JSON()),
        sa.UniqueConstraint("scenario_id", "user_id", "client_turn_id"),
    )
    op.create_index(
        "ix_app_text_turns_user_created", "app_text_turns", ["scenario_id", "user_id", "created_at"]
    )


def downgrade():
    op.drop_table("app_text_turns")
