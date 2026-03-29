from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from uuid import UUID
from core.database import get_db
from modules.auth.dependencies import current_user, require_advisor
from modules.auth.models import User, UserRole
from .models import Project, ProjectMember
from .schemas import ProjectCreate, ProjectUpdate, ProjectResponse, AddMemberRequest, MemberResponse
from .dependencies import check_project_access

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
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
    user: User = Depends(current_user),
):
    return await check_project_access(project_id, user, db)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    project = await check_project_access(project_id, user, db)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


# --- Project Member Management ---


@router.get("/{project_id}/members", response_model=list[MemberResponse])
async def list_members(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await db.execute(
        select(
            ProjectMember.id,
            ProjectMember.user_id,
            User.email,
            User.full_name,
            User.role,
            ProjectMember.added_at,
        )
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.added_at)
    )
    return [
        MemberResponse(
            id=row.id, user_id=row.user_id, email=row.email,
            full_name=row.full_name, role=row.role, added_at=row.added_at,
        )
        for row in result.all()
    ]


@router.post("/{project_id}/members", response_model=MemberResponse, status_code=201)
async def add_member(
    project_id: UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)

    target_user = await db.scalar(select(User).where(User.email == data.email))
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found with that email")

    already_member = await db.scalar(
        select(exists().where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.id,
        ))
    )
    if already_member:
        raise HTTPException(status_code=409, detail="User is already a project member")

    member = ProjectMember(project_id=project_id, user_id=target_user.id)
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return MemberResponse(
        id=member.id, user_id=target_user.id, email=target_user.email,
        full_name=target_user.full_name, role=target_user.role, added_at=member.added_at,
    )


@router.delete("/{project_id}/members/{user_id}", status_code=204)
async def remove_member(
    project_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    project = await check_project_access(project_id, user, db)

    if project.created_by == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the project creator")

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(member)
    await db.commit()
