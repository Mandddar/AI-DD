from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from .models import Workstream, DocumentStatus, TagSource


class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    uploaded_by: UUID
    name: str
    original_filename: str
    mime_type: str
    size_bytes: int
    workstream: Workstream
    status: DocumentStatus
    page_count: Optional[str]
    version_number: int = 1
    parent_doc_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentTextResponse(BaseModel):
    document_id: UUID
    content: str
    extracted_at: datetime

    model_config = {"from_attributes": True}


class StatusUpdateRequest(BaseModel):
    status: DocumentStatus


class DocumentTagResponse(BaseModel):
    id: UUID
    document_id: UUID
    tag: str
    confidence: Optional[float]
    source: TagSource
    created_at: datetime

    model_config = {"from_attributes": True}


class AddTagRequest(BaseModel):
    tag: str


class SearchResultResponse(BaseModel):
    id: UUID
    name: str
    original_filename: str
    workstream: Workstream
    status: DocumentStatus
    snippet: str
    rank: float
    created_at: datetime

    model_config = {"from_attributes": True}
