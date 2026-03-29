"""
Planning Module — API endpoints for the 5-phase interactive audit planning process.

Tech: FastAPI + Groq API + openpyxl (Excel export) + jinja2 (prompt templates)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import current_user as get_current_user
from modules.auth.models import User
from .models import AuditPlan, RequestListItem, PlanningPhase
from .schemas import BasicDataInput, DialogAnswer, RequestItemUpdate, AuditPlanOut, RequestItemOut
from .service import generate_risk_analysis, generate_dialog_questions, generate_audit_plan, generate_request_list_items

router = APIRouter(prefix="/projects/{project_id}/planning", tags=["planning"])


@router.post("/basic-data", response_model=AuditPlanOut, status_code=status.HTTP_201_CREATED)
async def submit_basic_data(
    project_id: UUID,
    data: BasicDataInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Phase 1: Submit basic company data — auto-advances to Phase 2 with AI risk analysis."""
    result = await db.execute(
        select(AuditPlan).where(AuditPlan.project_id == project_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Audit plan already exists for this project")

    basic_data = data.model_dump()

    # Generate risk analysis (Phase 2 content) immediately
    risk_analysis = await generate_risk_analysis(basic_data)

    plan = AuditPlan(
        project_id=project_id,
        created_by=user.id,
        current_phase=PlanningPhase.risk_analysis,  # Auto-advance to Phase 2
        basic_data=basic_data,
        risk_analysis=risk_analysis,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/", response_model=AuditPlanOut | None)
async def get_audit_plan(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the current audit plan for a project. Returns null if none exists."""
    result = await db.execute(
        select(AuditPlan).where(AuditPlan.project_id == project_id)
    )
    return result.scalar_one_or_none()


@router.post("/advance-phase", response_model=AuditPlanOut)
async def advance_phase(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Advance the audit plan to the next phase (triggers AI processing for the new phase)."""
    result = await db.execute(
        select(AuditPlan).where(AuditPlan.project_id == project_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="No audit plan found")

    phase_order = list(PlanningPhase)
    current_idx = phase_order.index(plan.current_phase)
    if current_idx >= len(phase_order) - 1:
        raise HTTPException(status_code=400, detail="Already at final phase")

    next_phase = phase_order[current_idx + 1]

    # Generate AI content for the next phase
    if next_phase == PlanningPhase.risk_analysis:
        plan.risk_analysis = await generate_risk_analysis(plan.basic_data or {})
    elif next_phase == PlanningPhase.dialog:
        plan.dialog_history = await generate_dialog_questions(
            plan.basic_data or {}, plan.risk_analysis or []
        )
    elif next_phase == PlanningPhase.plan_approval:
        plan.audit_plan_content = await generate_audit_plan(
            plan.basic_data or {}, plan.risk_analysis or [], plan.dialog_history or []
        )
    elif next_phase == PlanningPhase.request_list:
        # Generate request list items
        items = generate_request_list_items(plan.basic_data or {}, plan.risk_analysis or [])
        for idx, item_data in enumerate(items, start=1):
            db.add(RequestListItem(
                audit_plan_id=plan.id,
                item_number=idx,
                **item_data,
            ))

    plan.current_phase = next_phase
    await db.commit()
    await db.refresh(plan)
    return plan


@router.post("/approve", response_model=AuditPlanOut)
async def approve_plan(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Phase 4: Human approves the audit plan — generates request list and advances to Phase 5."""
    result = await db.execute(
        select(AuditPlan).where(AuditPlan.project_id == project_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="No audit plan found")

    from datetime import datetime, timezone
    plan.is_approved = True
    plan.approved_by = user.id
    plan.approved_at = datetime.now(timezone.utc)

    # Generate request list items on approval
    existing_items = await db.execute(
        select(RequestListItem).where(RequestListItem.audit_plan_id == plan.id).limit(1)
    )
    if not existing_items.scalar_one_or_none():
        items = generate_request_list_items(plan.basic_data or {}, plan.risk_analysis or [])
        for idx, item_data in enumerate(items, start=1):
            db.add(RequestListItem(
                audit_plan_id=plan.id,
                item_number=idx,
                **item_data,
            ))

    plan.current_phase = PlanningPhase.request_list
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/request-list", response_model=list[RequestItemOut])
async def get_request_list(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all request list items for this project's audit plan."""
    plan_result = await db.execute(
        select(AuditPlan).where(AuditPlan.project_id == project_id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="No audit plan found")

    result = await db.execute(
        select(RequestListItem)
        .where(RequestListItem.audit_plan_id == plan.id)
        .order_by(RequestListItem.item_number)
    )
    return list(result.scalars().all())


@router.patch("/request-list/{item_id}", response_model=RequestItemOut)
async def update_request_item(
    project_id: UUID,
    item_id: UUID,
    update: RequestItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update status/priority of a request list item."""
    item = await db.get(RequestListItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Request item not found")

    if update.status is not None:
        item.status = update.status
    if update.priority is not None:
        item.priority = update.priority
    if update.answer_document is not None:
        item.answer_document = update.answer_document

    await db.commit()
    await db.refresh(item)
    return item
