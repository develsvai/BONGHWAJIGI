"""앱 설치 계정의 회전 refresh 세션.

Revision ID: f735a2ec901b
Revises: bde1925b1429
"""

import sqlalchemy as sa
from alembic import op

revision = "f735a2ec901b"
down_revision = "bde1925b1429"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario_id", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("installation_id", sa.String(128), nullable=False),
        sa.Column("account_version", sa.Integer(), nullable=False),
        sa.Column("refresh_digest", sa.String(64), nullable=False),
        sa.Column("client_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_app_sessions_scenario_id", "app_sessions", ["scenario_id"])
    op.create_index(
        "ix_app_sessions_client_created", "app_sessions", ["client_digest", "created_at"]
    )


def downgrade():
    op.drop_index("ix_app_sessions_client_created", table_name="app_sessions")
    op.drop_index("ix_app_sessions_scenario_id", table_name="app_sessions")
    op.drop_table("app_sessions")
