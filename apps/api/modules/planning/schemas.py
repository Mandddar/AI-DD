from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class BasicDataInput(BaseModel):
    """Phase 1 input — basic company data."""
    company_name: str
    legal_form: str          # GmbH, AG, KG, etc.
    registered_office: str
    industry: str
    employee_count: int
    revenue_size: str
    deal_type: str           # share_deal or asset_deal


class DialogAnswer(BaseModel):
    """Phase 3 — answer to an AI-generated question."""
    question_id: int
    answer: str


class RequestItemUpdate(BaseModel):
    """Update status/priority of a request list item."""
    status: Optional[str] = None
    priority: Optional[str] = None
    answer_document: Optional[str] = None


class AuditPlanOut(BaseModel):
    id: UUID
    project_id: UUID
    current_phase: str
    basic_data: Optional[dict] = None
    risk_analysis: Optional[list] = None
    dialog_history: Optional[list] = None
    audit_plan_content: Optional[dict] = None
    is_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestItemOut(BaseModel):
    id: UUID
    item_number: int
    workstream: str
    audit_field: str
    question: str
    answer_document: Optional[str] = None
    status: str
    priority: str

    model_config = {"from_attributes": True}
