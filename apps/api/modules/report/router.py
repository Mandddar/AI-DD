"""
Report Module — API endpoints for generating and managing DD reports.

Tech: FastAPI + python-docx + openpyxl + jinja2 + Groq API
Report types: Detailed Workstream, Executive Summary, Consolidated Overall
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import get_current_user
from modules.auth.models import User
from .models import Report, ReportType
from .schemas import ReportCreate, ReportContentUpdate, ReportOut

router = APIRouter(prefix="/projects/{project_id}/reports", tags=["reports"])


@router.post("/generate", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate_report(
    project_id: UUID,
    data: ReportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a new report (AI creates content, human reviews before export)."""
    report = Report(
        project_id=project_id,
        created_by=user.id,
        report_type=data.report_type,
        workstream=data.workstream,
        title=data.title,
        content={},  # Populated by report generation service
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/", response_model=list[ReportOut])
async def list_reports(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all reports for a project."""
    result = await db.execute(
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    project_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific report with its content."""
    report = await db.get(Report, report_id)
    if not report or report.project_id != project_id:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}/edit", response_model=ReportOut)
async def edit_report_content(
    project_id: UUID,
    report_id: UUID,
    update: ReportContentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Edit report content (executive summary editing before export)."""
    report = await db.get(Report, report_id)
    if not report or report.project_id != project_id:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.is_finalized:
        raise HTTPException(status_code=400, detail="Cannot edit finalized report")

    report.edited_content = update.edited_content
    await db.commit()
    await db.refresh(report)
    return report


@router.post("/{report_id}/finalize", response_model=ReportOut)
async def finalize_report(
    project_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Finalize report — generates the .docx file for download."""
    report = await db.get(Report, report_id)
    if not report or report.project_id != project_id:
        raise HTTPException(status_code=404, detail="Report not found")

    from datetime import datetime, timezone
    report.is_finalized = True
    report.finalized_by = user.id
    report.finalized_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(report)
    return report
