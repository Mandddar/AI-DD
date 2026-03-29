"""
Self-Improvement Module — API endpoints for viewing and managing improvement suggestions.

Tech: FastAPI + Groq API + PostgreSQL
All suggestions are read-only proposals — developer must approve before any change is made.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import current_user as get_current_user
from modules.auth.models import User
from .models import ImprovementSuggestion, UsagePattern, SuggestionStatus
from .schemas import SuggestionOut, SuggestionReview, UsagePatternOut

router = APIRouter(prefix="/self-improvement", tags=["self-improvement"])


@router.get("/suggestions", response_model=list[SuggestionOut])
async def list_suggestions(
    status: str | None = None,
    module: str | None = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all improvement suggestions (optionally filtered)."""
    query = select(ImprovementSuggestion).order_by(ImprovementSuggestion.created_at.desc())
    if status:
        query = query.where(ImprovementSuggestion.status == status)
    if module:
        query = query.where(ImprovementSuggestion.module == module)
    query = query.limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.patch("/suggestions/{suggestion_id}", response_model=SuggestionOut)
async def review_suggestion(
    suggestion_id: UUID,
    review: SuggestionReview,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Developer approves or rejects an improvement suggestion."""
    suggestion = await db.get(ImprovementSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    from datetime import datetime, timezone
    suggestion.status = review.status
    suggestion.reviewed_by = review.reviewed_by
    suggestion.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(suggestion)
    return suggestion


@router.get("/patterns", response_model=list[UsagePatternOut])
async def list_usage_patterns(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List observed usage patterns."""
    result = await db.execute(
        select(UsagePattern)
        .order_by(UsagePattern.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
