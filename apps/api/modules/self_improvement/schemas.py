from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SuggestionOut(BaseModel):
    id: UUID
    category: str
    module: str
    title: str
    rationale: str
    expected_benefit: str
    suggested_change: str
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SuggestionReview(BaseModel):
    """Developer approves or rejects a suggestion."""
    status: str  # approved or rejected
    reviewed_by: str


class UsagePatternOut(BaseModel):
    id: UUID
    pattern_type: str
    module: str
    description: str
    frequency: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
