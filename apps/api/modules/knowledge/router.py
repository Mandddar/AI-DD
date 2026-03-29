"""
Knowledge Module — API endpoints for per-project and cross-project knowledge.

Tech: FastAPI + PostgreSQL JSONB + Groq API + presidio-analyzer (PII anonymization)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import current_user as get_current_user
from modules.auth.models import User
from .models import ProjectKnowledge, CrossProjectKnowledge
from .schemas import ProjectKnowledgeOut, CrossProjectKnowledgeOut

router = APIRouter(tags=["knowledge"])


@router.get(
    "/projects/{project_id}/knowledge",
    response_model=list[ProjectKnowledgeOut],
)
async def get_project_knowledge(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all knowledge entries for a specific project."""
    result = await db.execute(
        select(ProjectKnowledge)
        .where(ProjectKnowledge.project_id == project_id)
        .order_by(ProjectKnowledge.created_at.desc())
    )
    return list(result.scalars().all())


@router.get(
    "/knowledge/cross-project",
    response_model=list[CrossProjectKnowledgeOut],
)
async def get_cross_project_knowledge(
    industry: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get anonymized cross-project knowledge (filtered by industry if specified)."""
    query = select(CrossProjectKnowledge).where(CrossProjectKnowledge.is_anonymized == True)
    if industry:
        query = query.where(CrossProjectKnowledge.industry == industry)
    query = query.order_by(CrossProjectKnowledge.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())
