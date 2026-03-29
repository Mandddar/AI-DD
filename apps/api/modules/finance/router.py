"""
Finance Module — API endpoints for financial data import, mapping, and variance analysis.

Tech: FastAPI + pandas + openpyxl + numpy + Groq API
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import get_current_user
from modules.auth.models import User
from .models import FinancialDataset, FinancialLineItem, VarianceAnalysis
from .schemas import FinancialDatasetOut, LineItemOut, VarianceAnalysisOut

router = APIRouter(prefix="/projects/{project_id}/finance", tags=["finance"])


@router.post("/upload", response_model=FinancialDatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_financial_data(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Import financial data from Excel (.xlsx) or TSV file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xls", "tsv", "csv"):
        raise HTTPException(status_code=400, detail="Supported formats: .xlsx, .xls, .tsv, .csv")

    file_bytes = await file.read()

    dataset = FinancialDataset(
        project_id=project_id,
        uploaded_by=user.id,
        name=file.filename,
        source_filename=file.filename,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=list[FinancialDatasetOut])
async def list_datasets(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all financial datasets for a project."""
    result = await db.execute(
        select(FinancialDataset)
        .where(FinancialDataset.project_id == project_id)
        .order_by(FinancialDataset.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/datasets/{dataset_id}/items", response_model=list[LineItemOut])
async def get_line_items(
    project_id: UUID,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all line items for a financial dataset."""
    result = await db.execute(
        select(FinancialLineItem)
        .where(FinancialLineItem.dataset_id == dataset_id)
        .order_by(FinancialLineItem.period, FinancialLineItem.account_number)
    )
    return list(result.scalars().all())


@router.get("/variance", response_model=list[VarianceAnalysisOut])
async def get_variance_analyses(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all variance analyses for a project."""
    result = await db.execute(
        select(VarianceAnalysis)
        .where(VarianceAnalysis.project_id == project_id)
        .order_by(VarianceAnalysis.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/variance/run", response_model=VarianceAnalysisOut, status_code=status.HTTP_201_CREATED)
async def run_variance_analysis(
    project_id: UUID,
    analysis_type: str = "internal_historical",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Trigger variance analysis (internal historical or external benchmark)."""
    analysis = VarianceAnalysis(
        project_id=project_id,
        analysis_type=analysis_type,
        results=[],  # Populated by finance agent
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis
