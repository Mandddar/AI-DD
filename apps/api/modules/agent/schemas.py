from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .models import RunStatus, AgentType, Severity, FindingStatus


class RunCreate(BaseModel):
    workstreams: list[str] = ["planning", "legal", "tax", "finance"]


class FindingReview(BaseModel):
    status: FindingStatus  # approved | rejected


class FindingResponse(BaseModel):
    id: UUID
    run_id: UUID
    agent_type: AgentType
    category: str
    title: str
    description: str
    severity: Severity
    source_doc_ids: list[str]
    source_excerpts: list[str]
    status: FindingStatus
    reviewer_id: Optional[UUID]
    reviewed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    id: UUID
    project_id: UUID
    triggered_by: UUID
    status: RunStatus
    workstreams: list[str]
    total_documents: int
    processed_documents: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    findings: list[FindingResponse] = []

    model_config = {"from_attributes": True}


class RunSummaryResponse(BaseModel):
    id: UUID
    project_id: UUID
    triggered_by: UUID
    status: RunStatus
    workstreams: list[str]
    total_documents: int
    processed_documents: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    finding_count: int = 0

    model_config = {"from_attributes": True}
