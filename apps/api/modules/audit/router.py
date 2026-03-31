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
from modules.auth.dependencies import current_user as get_current_user
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
    """Query audit logs. Admin sees all; Lead Advisor sees own logs only; others get 403."""
    from modules.auth.models import UserRole

    # Only admin and lead_advisor can access audit logs
    if user.role not in (UserRole.admin, UserRole.lead_advisor):
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Access denied. Audit trail is restricted to administrators."
        )

    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    # Lead advisors only see their own logs
    if user.role == UserRole.lead_advisor:
        query = query.where(AuditLog.user_id == user.id)
    elif user_id:
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
    """Get all audit logs related to a specific project. Admin and Lead Advisor only."""
    from modules.auth.models import UserRole
    if user.role not in (UserRole.admin, UserRole.lead_advisor):
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Access denied. Audit trail is restricted to administrators."
        )

    query = (
        select(AuditLog)
        .where(AuditLog.resource_id == str(project_id))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    # Lead advisors only see their own logs
    if user.role == UserRole.lead_advisor:
        query = query.where(AuditLog.user_id == user.id)

    result = await db.execute(query)
    return list(result.scalars().all())
