"""
Finance Module — models for financial data import, account mapping, and variance analysis.

Tech: SQLAlchemy + PostgreSQL
Libraries: pandas (data processing), openpyxl (Excel import/export), numpy (variance calc), Groq API
"""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Integer, Text, JSON, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class ChartOfAccounts(str, enum.Enum):
    skr03 = "SKR03"
    skr04 = "SKR04"
    custom = "custom"


class FinancialDataset(Base):
    """A financial dataset imported for a project (e.g., annual accounts, monthly BWA)."""
    __tablename__ = "financial_datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    name = Column(String(255), nullable=False)
    source_filename = Column(String(255), nullable=False)
    chart_of_accounts = Column(SAEnum(ChartOfAccounts), nullable=True)

    # Period range covered
    period_from = Column(Date, nullable=True)
    period_to = Column(Date, nullable=True)

    # Raw data stored as JSON for flexibility
    raw_data = Column(JSON, nullable=True)
    # AI-detected structure metadata
    structure_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class FinancialLineItem(Base):
    """Individual line items from imported financial data."""
    __tablename__ = "financial_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("financial_datasets.id"), nullable=False, index=True)

    account_number = Column(String(20), nullable=True)
    account_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # Revenue, COGS, OpEx, etc.

    period = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class VarianceAnalysis(Base):
    """Stores results of internal and external variance analysis."""
    __tablename__ = "variance_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)

    analysis_type = Column(String(50), nullable=False)  # internal_historical, external_benchmark
    results = Column(JSON, nullable=False)  # [{metric, current, prior, variance_pct, flag}, ...]
    generated_queries = Column(JSON, nullable=True)  # AI-generated follow-up queries

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
