"""
Audit Module — API endpoints for viewing and exporting audit trails.

Tech: FastAPI + SQLAlchemy events + openpyxl (Excel export)
Design: Read-only API — logs are created by middleware and event hooks, never by direct API calls.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import get_current_user
from modules.auth.models import User
from .models import AuditLog
from .schemas import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogOut])
async def get_audit_logs(
    user_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Query audit logs with optional filters. Admin-only in production."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/logs/project/{project_id}", response_model=list[AuditLogOut])
async def get_project_audit_logs(
    project_id: UUID,
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all audit logs related to a specific project."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.resource_id == str(project_id))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
