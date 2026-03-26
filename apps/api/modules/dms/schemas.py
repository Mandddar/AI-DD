from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from .models import Workstream, DocumentStatus


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
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentTextResponse(BaseModel):
    document_id: UUID
    content: str
    extracted_at: datetime

    model_config = {"from_attributes": True}
