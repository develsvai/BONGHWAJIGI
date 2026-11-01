from datetime import UTC, datetime
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from bonghwajigi.db.base import Base


def now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (UniqueConstraint("scenario_id", "kind", "external_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scenario_id: Mapped[str] = mapped_column(String(128), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    external_id: Mapped[str] = mapped_column(String(256))
    body_hash: Mapped[str] = mapped_column(String(64))
    body: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))
    result: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class AnalysisOutbox(Base):
    __tablename__ = "analysis_outbox"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("analysis_jobs.id"), unique=True)
    next_dispatch_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, index=True
    )
    dispatch_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))


class DocumentChunk(Base):
    __tablename__ = "retrieval_chunks"
    __table_args__ = (
        UniqueConstraint(
            "scenario_id", "document_id", "revision", "chunk_index", "embedding_revision"
        ),
        Index("ix_retrieval_scope", "scenario_id", "embedding_revision"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scenario_id: Mapped[str] = mapped_column(String(128))
    document_id: Mapped[str] = mapped_column(String(128))
    revision: Mapped[int] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer)
    disaster_type: Mapped[str] = mapped_column(String(32))
    source_kind: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[dict] = mapped_column(JSON)
    origin: Mapped[str] = mapped_column(String(32))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    embedding_model: Mapped[str] = mapped_column(String(128))
    embedding_revision: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
