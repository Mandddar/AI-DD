import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Integer, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from core.database import Base


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentType(str, enum.Enum):
    planning = "planning"
    legal = "legal"
    tax = "tax"
    finance = "finance"


class Severity(str, enum.Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FindingStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    status = Column(SAEnum(RunStatus), nullable=False, default=RunStatus.pending)
    workstreams = Column(JSON, nullable=False, default=list)  # ["planning", "legal", "tax", "finance"]

    total_documents = Column(Integer, default=0)
    processed_documents = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class AgentFinding(Base):
    __tablename__ = "agent_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False, index=True)

    agent_type = Column(SAEnum(AgentType), nullable=False)
    category = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SAEnum(Severity), nullable=False, default=Severity.medium)

    source_doc_ids = Column(JSON, nullable=False, default=list)   # [uuid str, ...]
    source_excerpts = Column(JSON, nullable=False, default=list)  # [str, ...]

    status = Column(SAEnum(FindingStatus), nullable=False, default=FindingStatus.pending_review)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class DocumentChunk(Base):
    """Document chunks with PostgreSQL full-text search (no vectors needed)."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    # PostgreSQL FTS tsvector column — populated via trigger or on insert
    search_vector = Column(TSVECTOR, nullable=True)

    __table_args__ = (
        Index("ix_document_chunks_search", "search_vector", postgresql_using="gin"),
    )
