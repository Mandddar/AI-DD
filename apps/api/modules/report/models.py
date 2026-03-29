"""
Report Module — models for generated reports (Word .docx, Excel .xlsx).

Tech: SQLAlchemy + PostgreSQL
Libraries: python-docx (Word generation), openpyxl (Excel), jinja2 (templates), Groq API
"""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class ReportType(str, enum.Enum):
    detailed_workstream = "detailed_workstream"   # Per-workstream (Legal/Tax/Finance)
    executive_summary = "executive_summary"       # Condensed, editable
    consolidated = "consolidated"                 # Cross-workstream overall report


class ReportFormat(str, enum.Enum):
    docx = "docx"
    xlsx = "xlsx"


class Report(Base):
    """Generated due diligence report."""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    report_type = Column(SAEnum(ReportType), nullable=False)
    report_format = Column(SAEnum(ReportFormat), nullable=False, default=ReportFormat.docx)
    workstream = Column(String(50), nullable=True)  # For detailed reports: legal, tax, finance

    title = Column(String(500), nullable=False)
    # Editable content — human can modify before export
    content = Column(JSON, nullable=False)  # Structured report sections
    # Human-edited version (executive summary)
    edited_content = Column(JSON, nullable=True)

    storage_path = Column(String(512), nullable=True)  # Path to generated file

    is_finalized = Column(Boolean, default=False)
    finalized_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
