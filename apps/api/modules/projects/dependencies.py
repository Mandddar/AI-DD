"""Shared project access checks — used by projects, DMS, and agent routers."""
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from modules.auth.models import User, UserRole
from .models import Project, ProjectMember


async def check_project_access(project_id: UUID, user: User, db: AsyncSession) -> Project:
    """Verify project exists and user has access (admin or project member)."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role == UserRole.admin:
        return project

    is_member = await db.scalar(
        select(exists().where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        ))
    )
    if not is_member:
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    return project
