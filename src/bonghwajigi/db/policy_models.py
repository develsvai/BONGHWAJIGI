from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from bonghwajigi.db.analysis_models import new_id, now
from bonghwajigi.db.base import Base


class PolicyScope(Base):
    __tablename__ = "policy_scopes"
    scenario_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    clock_revision: Mapped[int] = mapped_column(Integer, default=0)
    evaluation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PolicyEntity(Base):
    __tablename__ = "policy_entities"
    scenario_id: Mapped[str] = mapped_column(
        ForeignKey("policy_scopes.scenario_id"), primary_key=True
    )
    kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(260), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer)
    body_hash: Mapped[str] = mapped_column(String(64))
    body: Mapped[dict] = mapped_column(JSON)


class PolicyProjection(Base):
    __tablename__ = "policy_projections"
    __table_args__ = (UniqueConstraint("scenario_id", "user_id", "incident_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("policy_scopes.scenario_id"), index=True)
    user_id: Mapped[str] = mapped_column(String(128))
    incident_id: Mapped[str] = mapped_column(String(128))
    requested: Mapped[int] = mapped_column(Integer, default=1)
    applied: Mapped[int] = mapped_column(Integer, default=0)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    content: Mapped[dict | None] = mapped_column(JSON)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_check_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, index=True
    )
    error_code: Mapped[str | None] = mapped_column(String(80))


class PolicySnapshot(Base):
    __tablename__ = "policy_snapshots"
    projection_id: Mapped[str] = mapped_column(
        ForeignKey("policy_projections.id"), primary_key=True
    )
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content: Mapped[dict] = mapped_column(JSON)


class PolicyIntegration(Base):
    __tablename__ = "policy_integrations"
    __table_args__ = (UniqueConstraint("scenario_id", "incident_id", "incident_revision"),)
    job_id: Mapped[str] = mapped_column(ForeignKey("analysis_jobs.id"), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("policy_scopes.scenario_id"), index=True)
    incident_id: Mapped[str] = mapped_column(String(128))
    incident_revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="waiting_retrieval")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    lease_id: Mapped[str | None] = mapped_column(String(36))
    error_code: Mapped[str | None] = mapped_column(String(80))
    result: Mapped[dict | None] = mapped_column(JSON)
    raw_generation: Mapped[dict | None] = mapped_column(JSON)
    prompt: Mapped[str | None] = mapped_column(Text)
