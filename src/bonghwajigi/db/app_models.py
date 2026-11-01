from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.base import Base


class AppAccount(Base):
    __tablename__ = "app_accounts"
    scenario_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AppMutation(Base):
    __tablename__ = "app_mutations"
    scenario_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    resource: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(260), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AppSession(Base):
    __tablename__ = "app_sessions"
    __table_args__ = (Index("ix_app_sessions_client_created", "client_digest", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(128), index=True)
    user_id: Mapped[str] = mapped_column(String(128))
    installation_id: Mapped[str] = mapped_column(String(128))
    account_version: Mapped[int] = mapped_column(Integer)
    refresh_digest: Mapped[str] = mapped_column(String(64))
    client_digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppTextTurn(Base):
    __tablename__ = "app_text_turns"
    __table_args__ = (
        UniqueConstraint("scenario_id", "user_id", "client_turn_id"),
        Index("ix_app_text_turns_user_created", "scenario_id", "user_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[str] = mapped_column(String(128))
    response_id: Mapped[str] = mapped_column(
        ForeignKey("policy_projections.id", ondelete="CASCADE")
    )
    client_turn_id: Mapped[str] = mapped_column(String(128))
    session_id: Mapped[str | None] = mapped_column(String(36))
    token_version: Mapped[int] = mapped_column(Integer)
    fingerprint: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32))
    response_revision: Mapped[int] = mapped_column(Integer)
    context_revision: Mapped[int] = mapped_column(Integer)
    input_versions: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    result: Mapped[dict | None] = mapped_column(JSON)
