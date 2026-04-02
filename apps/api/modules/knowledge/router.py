"""
Knowledge Module — API endpoints for per-project and cross-project knowledge.

Tech: FastAPI + PostgreSQL JSONB
Features:
  - Per-project learning file (spec §10.1)
  - Cross-project anonymized knowledge base (spec §10.2)
  - Admin expandable knowledge base (spec §10.3)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import current_user as get_current_user, require_admin, require_advisor
from modules.auth.models import User
from .models import ProjectKnowledge, CrossProjectKnowledge
from .schemas import ProjectKnowledgeOut, CrossProjectKnowledgeOut, KnowledgeSourceCreate
from .service import populate_project_knowledge, sync_cross_project_knowledge

router = APIRouter(tags=["knowledge"])


# ── Per-Project Knowledge ──────────────────────────────────

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


@router.post(
    "/projects/{project_id}/knowledge/populate",
    response_model=list[ProjectKnowledgeOut],
)
async def populate_knowledge(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    """
    Populate per-project knowledge from approved agent findings (spec §10.1).
    Collects all audit findings and insights, creates knowledge entries.
    """
    entries = await populate_project_knowledge(db, project_id)
    return entries


@router.post(
    "/projects/{project_id}/knowledge",
    response_model=ProjectKnowledgeOut,
    status_code=201,
)
async def create_knowledge_entry(
    project_id: UUID,
    data: KnowledgeSourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    """Manually add a knowledge entry to a project (spec §10.3 — expandable knowledge base)."""
    entry = ProjectKnowledge(
        project_id=project_id,
        category=data.category,
        title=data.title,
        content=data.content,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


# ── Cross-Project Knowledge ────────────────────────────────

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


@router.post("/knowledge/cross-project/sync")
async def trigger_cross_project_sync(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """
    Admin-only: Sync cross-project knowledge (spec §10.2).
    Aggregates approved findings across all projects with anonymization.
    Removes: company names, personal names, addresses.
    Retains: numerical values, risk patterns, legal-form findings, issue frequency.
    """
    new_count = await sync_cross_project_knowledge(db)
    return {"message": f"Cross-project sync complete. {new_count} new entries created."}
