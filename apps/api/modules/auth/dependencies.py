"""
Auth dependencies — role-based and project-level access control.

Role hierarchy (from spec §4.1):
  Admin           → Full access to all features, projects, and settings
  Lead Advisor    → Creates projects, controls process, approves external communication
  Team Advisor    → Works on assigned workstreams within approved scope
  Seller          → Uploads documents, answers queries, views only their own areas
  Buyer/Investor  → Read-only access to approved documents and finalized reports
"""
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .models import User, UserRole
from .service import get_current_user

bearer = HTTPBearer()


async def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await get_current_user(db, credentials.credentials)


def require_role(*roles: UserRole):
    async def _check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _check


# ── Convenience shortcuts ─────────────────────────────────────
require_admin = require_role(UserRole.admin)
require_advisor = require_role(UserRole.admin, UserRole.lead_advisor, UserRole.team_advisor)


# ── Project-level access control ──────────────────────────────

async def _check_project_membership(project_id: UUID, user: User, db: AsyncSession) -> None:
    """Verify user is a member of the project. Admins bypass this check."""
    if user.role == UserRole.admin:
        return

    from modules.projects.models import ProjectMember
    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .where(ProjectMember.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project")


def require_project_member():
    """Dependency: user must be a member of the project (or admin)."""
    async def _check(
        project_id: UUID,
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        await _check_project_membership(project_id, user, db)
        return user
    return _check


def require_project_role(*roles: UserRole):
    """Dependency: user must be a project member AND have one of the specified global roles."""
    async def _check(
        project_id: UUID,
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # Admin always passes
        if user.role == UserRole.admin:
            return user
        # Check role first
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this action")
        # Then check membership
        await _check_project_membership(project_id, user, db)
        return user
    return _check


# ── Pre-built project-level permission sets ───────────────────

# Can manage project: create/edit deals, trigger analysis, generate reports, approve plans
project_manager = require_project_role(UserRole.lead_advisor, UserRole.team_advisor)

# Can write to project: upload docs, submit data (includes sellers)
project_contributor = require_project_role(UserRole.lead_advisor, UserRole.team_advisor, UserRole.seller)

# Can read project data (all member roles)
project_reader = require_project_member()
