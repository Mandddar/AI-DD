"""
Self-Improvement Module — observes usage patterns and generates code improvement suggestions.

Tech: SQLAlchemy + PostgreSQL
Libraries: Groq API (pattern analysis + fix suggestions)
Note: Reuses audit logs + Groq, no extra libraries needed.

All suggestions require developer approval — no autonomous code modifications.
"""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class SuggestionStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    implemented = "implemented"


class SuggestionCategory(str, enum.Enum):
    performance = "performance"
    accuracy = "accuracy"
    user_experience = "user_experience"
    prompt_optimization = "prompt_optimization"
    workflow = "workflow"


class UsagePattern(Base):
    """Observed usage patterns across projects."""
    __tablename__ = "usage_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    pattern_type = Column(String(100), nullable=False)  # manual_correction, adjustment, bottleneck
    module = Column(String(100), nullable=False)         # Which module is affected
    description = Column(Text, nullable=False)
    frequency = Column(String(20), nullable=True)        # How often this pattern occurs
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ImprovementSuggestion(Base):
    """AI-generated code improvement suggestions for developer review."""
    __tablename__ = "improvement_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    category = Column(SAEnum(SuggestionCategory), nullable=False)
    module = Column(String(100), nullable=False)         # Which module to change
    title = Column(String(500), nullable=False)
    rationale = Column(Text, nullable=False)             # Why this change is suggested
    expected_benefit = Column(Text, nullable=False)      # What improvement is expected
    suggested_change = Column(Text, nullable=False)      # Concrete code change proposal

    status = Column(SAEnum(SuggestionStatus), nullable=False, default=SuggestionStatus.proposed)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
