import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, String, DateTime, Date, Enum as SAEnum, ForeignKey,
    Integer, Float, Text, Boolean, Numeric, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class ChartOfAccounts(str, enum.Enum):
    skr03 = "skr03"
    skr04 = "skr04"
    custom = "custom"


class DatasetStatus(str, enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AnalysisType(str, enum.Enum):
    mom = "mom"
    yoy = "yoy"
    trend = "trend"
    benchmark = "benchmark"


class VarianceSignificance(str, enum.Enum):
    normal = "normal"
    notable = "notable"
    significant = "significant"
    critical = "critical"


class FinanceQueryStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class PnlSection(str, enum.Enum):
    revenue = "revenue"
    cost_of_goods = "cost_of_goods"
    personnel = "personnel"
    other_operating = "other_operating"
    depreciation = "depreciation"
    interest = "interest"
    tax = "tax"
    other = "other"


class FinancialDataset(Base):
    """One row per import event (one uploaded file)."""
    __tablename__ = "financial_datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    chart_of_accounts = Column(SAEnum(ChartOfAccounts), nullable=False, default=ChartOfAccounts.custom)
    source_filename = Column(String(255), nullable=False)
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    row_count = Column(Integer, default=0)
    status = Column(SAEnum(DatasetStatus), nullable=False, default=DatasetStatus.processing)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FinancialLineItem(Base):
    """Individual account + period + amount."""
    __tablename__ = "financial_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("financial_datasets.id"), nullable=False)
    account_code = Column(String(20), nullable=False)
    account_name = Column(String(255), nullable=False)
    standardized_category = Column(String(100), nullable=True)
    period = Column(Date, nullable=False)  # normalized to first-of-month
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "account_code", "period", name="uq_line_item_project_account_period"),
        Index("ix_line_items_project_period_category", "project_id", "period", "standardized_category"),
    )


class AccountMapping(Base):
    """Reference table for SKR03/SKR04 chart-of-accounts mapping (seeded)."""
    __tablename__ = "account_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chart_type = Column(SAEnum(ChartOfAccounts), nullable=False)
    account_code_start = Column(String(10), nullable=False)
    account_code_end = Column(String(10), nullable=False)
    standardized_category = Column(String(100), nullable=False)
    display_name_de = Column(String(255), nullable=False)
    display_name_en = Column(String(255), nullable=False)
    is_revenue = Column(Boolean, default=False, nullable=False)
    is_cost = Column(Boolean, default=False, nullable=False)
    pnl_section = Column(SAEnum(PnlSection), nullable=False)


class VarianceResult(Base):
    """Computed variance analysis output."""
    __tablename__ = "variance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    analysis_type = Column(SAEnum(AnalysisType), nullable=False)
    standardized_category = Column(String(100), nullable=True)
    period = Column(Date, nullable=False)
    comparison_period = Column(Date, nullable=True)
    variance_pct = Column(Float, nullable=True)
    variance_abs = Column(Numeric(15, 2), nullable=True)
    significance = Column(SAEnum(VarianceSignificance), nullable=False, default=VarianceSignificance.normal)
    ai_commentary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class BenchmarkData(Base):
    """External industry benchmarks (admin-managed)."""
    __tablename__ = "benchmark_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    industry = Column(String(255), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    source = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FinanceQuery(Base):
    """Auto-generated follow-up questions with HITL approval."""
    __tablename__ = "finance_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    variance_id = Column(UUID(as_uuid=True), ForeignKey("variance_results.id"), nullable=True)
    question = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    status = Column(SAEnum(FinanceQueryStatus), nullable=False, default=FinanceQueryStatus.pending_review)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
