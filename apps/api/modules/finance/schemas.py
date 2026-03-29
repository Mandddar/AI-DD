from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from .models import ChartOfAccounts, DatasetStatus, AnalysisType, VarianceSignificance, FinanceQueryStatus


class DatasetResponse(BaseModel):
    id: UUID
    project_id: UUID
    chart_of_accounts: ChartOfAccounts
    source_filename: str
    imported_by: UUID
    period_start: Optional[date]
    period_end: Optional[date]
    row_count: int
    status: DatasetStatus
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LineItemResponse(BaseModel):
    id: UUID
    account_code: str
    account_name: str
    standardized_category: Optional[str]
    period: date
    amount: Decimal
    currency: str

    model_config = {"from_attributes": True}


class PeriodSummary(BaseModel):
    period: date
    total_revenue: Decimal
    total_costs: Decimal
    ebitda: Decimal


class CategoryPeriodAmount(BaseModel):
    standardized_category: str
    period: date
    amount: Decimal


class FinancialSummaryResponse(BaseModel):
    periods: list[date]
    categories: list[str]
    data: list[CategoryPeriodAmount]
    period_summaries: list[PeriodSummary]


class VarianceResultResponse(BaseModel):
    id: UUID
    analysis_type: AnalysisType
    standardized_category: Optional[str]
    period: date
    comparison_period: Optional[date]
    variance_pct: Optional[float]
    variance_abs: Optional[Decimal]
    significance: VarianceSignificance
    ai_commentary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendDataPoint(BaseModel):
    period: date
    amount: Decimal


class TrendResponse(BaseModel):
    category: str
    direction: str  # "growing", "declining", "stable"
    avg_growth_rate: Optional[float]
    data_points: list[TrendDataPoint]


class BenchmarkComparison(BaseModel):
    metric_name: str
    company_value: float
    industry_value: float
    delta: float
    source: str
    year: int


class FinanceQueryResponse(BaseModel):
    id: UUID
    project_id: UUID
    variance_id: Optional[UUID]
    question: str
    context: Optional[str]
    status: FinanceQueryStatus
    approved_by: Optional[UUID]
    reviewed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryReviewRequest(BaseModel):
    status: FinanceQueryStatus
