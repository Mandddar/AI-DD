from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class FinancialDatasetOut(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    source_filename: str
    chart_of_accounts: Optional[str] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LineItemOut(BaseModel):
    id: UUID
    account_number: Optional[str] = None
    account_name: str
    category: Optional[str] = None
    period: date
    amount: float
    currency: str

    model_config = {"from_attributes": True}


class VarianceAnalysisOut(BaseModel):
    id: UUID
    project_id: UUID
    analysis_type: str
    results: list
    generated_queries: Optional[list] = None
    created_at: datetime

    model_config = {"from_attributes": True}
