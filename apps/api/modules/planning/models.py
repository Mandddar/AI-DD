"""
Planning Module — models for audit planning, interactive dialog, and request lists.

Tech: SQLAlchemy + PostgreSQL (shared DB)
Libraries: Groq API (planning agent LLM), openpyxl (Excel export), jinja2 (prompt templates)
"""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Integer, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class PlanningPhase(str, enum.Enum):
    basic_data = "basic_data"           # Phase 1: Basic data collection
    risk_analysis = "risk_analysis"     # Phase 2: AI risk analysis
    dialog = "dialog"                   # Phase 3: Interactive dialog
    plan_approval = "plan_approval"     # Phase 4: Audit plan approval
    request_list = "request_list"       # Phase 5: Request list generation


class RequestItemStatus(str, enum.Enum):
    open = "open"
    partial = "partial"
    query = "query"
    completed = "completed"


class RequestItemPriority(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AuditPlan(Base):
    """Audit plan for a project — created through the 5-phase planning process."""
    __tablename__ = "audit_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, unique=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    current_phase = Column(SAEnum(PlanningPhase), nullable=False, default=PlanningPhase.basic_data)

    # Phase 1 — basic data (stored as JSON for flexibility)
    basic_data = Column(JSON, nullable=True)  # {company_name, legal_form, industry, ...}

    # Phase 2 — AI-generated risk analysis
    risk_analysis = Column(JSON, nullable=True)  # [{risk_area, description, severity}, ...]

    # Phase 3 — dialog Q&A history
    dialog_history = Column(JSON, nullable=True, default=list)  # [{question, answer}, ...]

    # Phase 4 — final audit plan (approved by human)
    audit_plan_content = Column(JSON, nullable=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class RequestListItem(Base):
    """Individual item on the due diligence request list (Phase 5)."""
    __tablename__ = "request_list_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_plan_id = Column(UUID(as_uuid=True), ForeignKey("audit_plans.id"), nullable=False, index=True)

    item_number = Column(Integer, nullable=False)
    workstream = Column(String(50), nullable=False)    # Legal, Tax, Finance
    audit_field = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    answer_document = Column(Text, nullable=True)

    status = Column(SAEnum(RequestItemStatus), nullable=False, default=RequestItemStatus.open)
    priority = Column(SAEnum(RequestItemPriority), nullable=False, default=RequestItemPriority.medium)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
