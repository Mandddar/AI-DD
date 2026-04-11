from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from core.database import get_db
from modules.auth.dependencies import current_user, require_advisor, require_role, project_manager, project_reader
from modules.auth.models import User as UserModel, UserRole
from .models import Project, ProjectMember, ProjectStatus
from .schemas import ProjectCreate, ProjectUpdate, ProjectResponse

User = UserModel


class AddMemberRequest(BaseModel):
    user_email: str

router = APIRouter(prefix="/projects", tags=["projects"])


require_project_creator = require_role(UserRole.admin, UserRole.lead_advisor)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project_creator),
):
    project = Project(**data.model_dump(), created_by=user.id)
    db.add(project)
    await db.flush()

    member = ProjectMember(project_id=project.id, user_id=user.id)
    db.add(member)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    # Admins see all; others see only their projects
    if user.role.value == "admin":
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    else:
        result = await db.execute(
            select(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/complete/vote", response_model=dict)
async def vote_deal_completion(
    project_id: UUID,
    vote: str = "approved",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Vote to approve or reject deal completion. All members can vote."""
    from datetime import datetime, timezone as tz
    member = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .where(ProjectMember.user_id == user.id)
    )
    membership = member.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    if vote not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Vote must be 'approved' or 'rejected'")

    membership.completion_approved = vote
    membership.completion_voted_at = datetime.now(tz.utc)
    await db.commit()

    # Check if all members have approved
    all_members = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    members = list(all_members.scalars().all())
    total = len(members)
    approved = sum(1 for m in members if m.completion_approved == "approved")
    rejected = sum(1 for m in members if m.completion_approved == "rejected")

    # Auto-complete if all approved
    if approved == total:
        project = await db.get(Project, project_id)
        if project:
            project.status = ProjectStatus.completed
            await db.commit()

    return {
        "total_members": total,
        "approved": approved,
        "rejected": rejected,
        "pending": total - approved - rejected,
        "deal_completed": approved == total,
    }


@router.get("/{project_id}/complete/status")
async def get_completion_status(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """Get deal completion voting status."""
    result = await db.execute(
        select(
            ProjectMember.user_id,
            ProjectMember.completion_approved,
            ProjectMember.completion_voted_at,
            UserModel.full_name,
            UserModel.email,
            UserModel.role,
        )
        .join(UserModel, UserModel.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
    )
    members = result.all()
    total = len(members)
    approved = sum(1 for m in members if m.completion_approved == "approved")

    return {
        "total_members": total,
        "approved": approved,
        "rejected": sum(1 for m in members if m.completion_approved == "rejected"),
        "pending": total - sum(1 for m in members if m.completion_approved is not None),
        "deal_completed": approved == total,
        "votes": [
            {
                "user_id": str(m.user_id),
                "name": m.full_name,
                "email": m.email,
                "role": m.role.value if m.role else None,
                "vote": m.completion_approved,
                "voted_at": m.completion_voted_at.isoformat() if m.completion_voted_at else None,
            }
            for m in members
        ],
    }


@router.post("/{project_id}/members", status_code=201)
async def add_member(
    project_id: UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Look up the user by email
    result = await db.execute(select(User).where(User.email == data.user_email))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    existing = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .where(ProjectMember.user_id == target_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member of this project")

    member = ProjectMember(project_id=project_id, user_id=target_user.id)
    db.add(member)
    await db.commit()
    return {"detail": "Member added", "user_id": str(target_user.id), "project_id": str(project_id)}
