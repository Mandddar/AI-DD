from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.database import get_db
from modules.auth.dependencies import current_user, require_advisor
from modules.auth.models import User
from modules.projects.dependencies import check_project_access
from .models import AgentRun, AgentFinding, FindingStatus
from .schemas import RunCreate, RunResponse, RunSummaryResponse, FindingReview, FindingResponse
from .orchestrator import run_analysis

router = APIRouter(prefix="/projects/{project_id}/agent", tags=["agents"])


@router.post("/runs", response_model=RunSummaryResponse, status_code=201)
async def trigger_run(
    project_id: UUID,
    data: RunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)
    valid = {"planning", "legal", "tax", "finance"}
    workstreams = [w for w in data.workstreams if w in valid]
    if not workstreams:
        raise HTTPException(status_code=422, detail="At least one valid workstream required")

    run = AgentRun(
        project_id=project_id,
        triggered_by=user.id,
        workstreams=workstreams,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background_tasks.add_task(run_analysis, run.id)

    return RunSummaryResponse(
        **{c.key: getattr(run, c.key) for c in run.__table__.columns},
        finding_count=0,
    )


@router.get("/runs", response_model=list[RunSummaryResponse])
async def list_runs(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    runs_result = await db.execute(
        select(AgentRun)
        .where(AgentRun.project_id == project_id)
        .order_by(AgentRun.created_at.desc())
    )
    runs = list(runs_result.scalars().all())

    summaries = []
    for run in runs:
        count_result = await db.execute(
            select(func.count()).where(AgentFinding.run_id == run.id)
        )
        count = count_result.scalar_one()
        summaries.append(RunSummaryResponse(
            **{c.key: getattr(run, c.key) for c in run.__table__.columns},
            finding_count=count,
        ))
    return summaries


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    project_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    run = await db.get(AgentRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(status_code=404, detail="Run not found")

    findings_result = await db.execute(
        select(AgentFinding)
        .where(AgentFinding.run_id == run_id)
        .order_by(AgentFinding.agent_type, AgentFinding.severity.desc())
    )
    findings = list(findings_result.scalars().all())

    return RunResponse(
        **{c.key: getattr(run, c.key) for c in run.__table__.columns},
        findings=[FindingResponse.model_validate(f) for f in findings],
    )


@router.patch("/runs/{run_id}/findings/{finding_id}", response_model=FindingResponse)
async def review_finding(
    project_id: UUID,
    run_id: UUID,
    finding_id: UUID,
    data: FindingReview,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)
    finding = await db.get(AgentFinding, finding_id)
    if not finding or finding.run_id != run_id:
        raise HTTPException(status_code=404, detail="Finding not found")

    if data.status not in (FindingStatus.approved, FindingStatus.rejected):
        raise HTTPException(status_code=422, detail="Status must be approved or rejected")

    finding.status = data.status
    finding.reviewer_id = user.id
    finding.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(finding)
    return finding
