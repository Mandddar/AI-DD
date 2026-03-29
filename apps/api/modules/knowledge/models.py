"""
Knowledge Module — per-project learning file + cross-project anonymized knowledge base.

Tech: SQLAlchemy + PostgreSQL (JSONB for flexible knowledge storage)
Libraries: Groq API (pattern analysis), presidio-analyzer (PII detection for anonymization)
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from core.database import Base


class ProjectKnowledge(Base):
    """Per-project learning file — collects findings, insights, risk updates."""
    __tablename__ = "project_knowledge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)

    category = Column(String(100), nullable=False)  # risk_finding, insight, pattern, risk_update
    workstream = Column(String(50), nullable=True)   # legal, tax, finance
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)

    # Structured data (JSONB for flexible queries)
    metadata = Column(JSONB, nullable=True)  # {severity, confidence, source_docs, ...}

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CrossProjectKnowledge(Base):
    """Anonymized cross-project knowledge base — no PII, only patterns and metrics."""
    __tablename__ = "cross_project_knowledge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    industry = Column(String(100), nullable=False)
    legal_form = Column(String(50), nullable=True)
    company_size = Column(String(50), nullable=True)  # small, medium, large

    pattern_type = Column(String(100), nullable=False)  # risk_pattern, finding_frequency, benchmark
    description = Column(Text, nullable=False)

    # Anonymized metrics (JSONB)
    metrics = Column(JSONB, nullable=False)  # {occurrence_rate, avg_severity, ...}

    is_anonymized = Column(Boolean, default=True, nullable=False)

    source_project_count = Column(String(10), nullable=True)  # How many projects contributed

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
