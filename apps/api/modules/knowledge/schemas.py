from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ProjectKnowledgeOut(BaseModel):
    id: UUID
    project_id: UUID
    category: str
    workstream: Optional[str] = None
    title: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CrossProjectKnowledgeOut(BaseModel):
    id: UUID
    industry: str
    legal_form: Optional[str] = None
    pattern_type: str
    description: str
    metrics: dict
    source_project_count: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSourceCreate(BaseModel):
    """Admin adds additional knowledge source."""
    title: str
    content: str
    category: str  # legal_reference, regulatory_guidance, etc.
