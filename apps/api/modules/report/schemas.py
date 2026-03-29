from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ReportCreate(BaseModel):
    report_type: str        # detailed_workstream, executive_summary, consolidated
    workstream: Optional[str] = None  # For detailed: legal, tax, finance
    title: str


class ReportContentUpdate(BaseModel):
    """Update editable content (executive summary editing)."""
    edited_content: dict


class ReportOut(BaseModel):
    id: UUID
    project_id: UUID
    report_type: str
    report_format: str
    workstream: Optional[str] = None
    title: str
    content: dict
    edited_content: Optional[dict] = None
    is_finalized: bool
    storage_path: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
