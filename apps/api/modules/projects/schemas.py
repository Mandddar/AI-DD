from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from .models import DealType, ProjectStatus, LegalForm


class ProjectCreate(BaseModel):
    name: str
    company_name: str
    legal_form: LegalForm = LegalForm.gmbh
    industry: Optional[str] = None
    employee_count: Optional[str] = None
    revenue_size: Optional[str] = None
    registered_office: Optional[str] = None
    deal_type: DealType = DealType.share_deal
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ProjectStatus] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    company_name: str
    legal_form: LegalForm
    industry: Optional[str]
    employee_count: Optional[str]
    revenue_size: Optional[str]
    registered_office: Optional[str]
    deal_type: DealType
    status: ProjectStatus
    description: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
