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
from modules.auth.dependencies import current_user as get_current_user
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

    # Generate .docx file
    from datetime import datetime, timezone
    docx_path = _generate_docx(report)
    report.storage_path = docx_path
    report.is_finalized = True
    report.finalized_by = user.id
    report.finalized_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{report_id}/download")
async def download_report(
    project_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download finalized report as .docx."""
    report = await db.get(Report, report_id)
    if not report or report.project_id != project_id:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.storage_path:
        raise HTTPException(status_code=400, detail="Report file not yet generated. Finalize the report first.")

    import os
    if not os.path.exists(report.storage_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in report.title)
    return FileResponse(
        path=report.storage_path,
        filename=f"{safe_title}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def _generate_docx(report) -> str:
    """Generate a Word .docx file from report content."""
    from docx import Document as DocxDocument
    from pathlib import Path
    import uuid

    doc = DocxDocument()

    # Title
    doc.add_heading(report.title, level=0)

    # AI Disclaimer
    disclaimer = doc.add_paragraph()
    disclaimer.add_run(
        "Notice: This report uses Artificial Intelligence to support the due diligence review. "
        "AI-generated results may be inaccurate, incomplete, or misleading. Responsibility for "
        "audit results lies exclusively with the human reviewer."
    ).italic = True

    doc.add_paragraph("")

    # Report metadata
    from datetime import datetime, timezone
    meta = doc.add_paragraph()
    meta.add_run(f"Report Type: ").bold = True
    meta.add_run(f"{report.report_type}\n")
    if report.workstream:
        meta.add_run(f"Workstream: ").bold = True
        meta.add_run(f"{report.workstream}\n")
    meta.add_run(f"Generated: ").bold = True
    meta.add_run(f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    doc.add_paragraph("")

    # Content — use edited_content if available, otherwise content
    content = report.edited_content or report.content or {}
    if isinstance(content, dict):
        for section_title, section_body in content.items():
            doc.add_heading(section_title, level=1)
            if isinstance(section_body, str):
                doc.add_paragraph(section_body)
            elif isinstance(section_body, list):
                for item in section_body:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            p = doc.add_paragraph()
                            p.add_run(f"{k}: ").bold = True
                            p.add_run(str(v))
                    else:
                        doc.add_paragraph(str(item), style="List Bullet")
            elif isinstance(section_body, dict):
                for k, v in section_body.items():
                    p = doc.add_paragraph()
                    p.add_run(f"{k}: ").bold = True
                    p.add_run(str(v))
            else:
                doc.add_paragraph(str(section_body))
    else:
        doc.add_paragraph(str(content))

    # Save
    uploads_dir = Path(__file__).parent.parent.parent / "uploads" / "reports"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    filepath = uploads_dir / f"{uuid.uuid4()}.docx"
    doc.save(str(filepath))
    return str(filepath)
