import logging
from datetime import datetime, timezone, date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, text

from core.database import get_db
from modules.auth.dependencies import current_user, require_advisor
from modules.auth.models import User
from modules.projects.dependencies import check_project_access
from modules.projects.models import Project

from .models import (
    FinancialDataset, FinancialLineItem, VarianceResult, FinanceQuery,
    DatasetStatus, FinanceQueryStatus, VarianceSignificance,
)
from .schemas import (
    DatasetResponse, LineItemResponse, FinancialSummaryResponse,
    CategoryPeriodAmount, PeriodSummary, VarianceResultResponse,
    TrendResponse, BenchmarkComparison, FinanceQueryResponse,
    QueryReviewRequest,
)
from .importer import process_financial_import
from .analysis import run_variance_analysis, compute_trend, compute_benchmarks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/finance", tags=["finance"])

FINANCE_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/tab-separated-values",
    "text/plain",
}


# --- Import ---

@router.post("/import", response_model=DatasetResponse, status_code=201)
async def import_financial_data(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)

    file_bytes = await file.read()
    mime = file.content_type or "application/octet-stream"
    if mime not in FINANCE_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime}. Use Excel (.xlsx) or TSV.")

    dataset = FinancialDataset(
        project_id=project_id,
        source_filename=file.filename or "import",
        imported_by=user.id,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    background_tasks.add_task(
        process_financial_import, dataset.id, file_bytes, file.filename or "import.xlsx", project_id,
    )

    return dataset


@router.post("/append", response_model=DatasetResponse, status_code=201)
async def append_financial_data(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    """Append new monthly data. Uses UPSERT — newer data wins for overlapping periods."""
    await check_project_access(project_id, user, db)

    file_bytes = await file.read()
    mime = file.content_type or "application/octet-stream"
    if mime not in FINANCE_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime}")

    dataset = FinancialDataset(
        project_id=project_id,
        source_filename=file.filename or "append",
        imported_by=user.id,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    background_tasks.add_task(
        process_financial_import, dataset.id, file_bytes, file.filename or "append.xlsx", project_id,
    )

    return dataset


# --- Datasets ---

@router.get("/datasets", response_model=list[DatasetResponse])
async def list_datasets(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await db.execute(
        select(FinancialDataset)
        .where(FinancialDataset.project_id == project_id)
        .order_by(FinancialDataset.created_at.desc())
    )
    return result.scalars().all()


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    project_id: UUID,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    dataset = await db.get(FinancialDataset, dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=204)
async def delete_dataset(
    project_id: UUID,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)
    dataset = await db.get(FinancialDataset, dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    await db.execute(
        delete(FinancialLineItem).where(FinancialLineItem.dataset_id == dataset_id)
    )
    await db.delete(dataset)
    await db.commit()


# --- Financial Data ---

@router.get("/data", response_model=list[LineItemResponse])
async def list_line_items(
    project_id: UUID,
    period_from: date | None = Query(None),
    period_to: date | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    query = select(FinancialLineItem).where(FinancialLineItem.project_id == project_id)
    if period_from:
        query = query.where(FinancialLineItem.period >= period_from)
    if period_to:
        query = query.where(FinancialLineItem.period <= period_to)
    if category:
        query = query.where(FinancialLineItem.standardized_category == category)
    query = query.order_by(FinancialLineItem.period, FinancialLineItem.account_code).limit(5000)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/data/summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """P&L summary: categories as rows, periods as columns."""
    await check_project_access(project_id, user, db)

    # Get aggregated data
    result = await db.execute(text("""
        SELECT standardized_category, period, SUM(amount) AS amount
        FROM financial_line_items
        WHERE project_id = :pid AND standardized_category IS NOT NULL
        GROUP BY standardized_category, period
        ORDER BY period, standardized_category
    """).bindparams(pid=project_id))

    rows = result.mappings().all()
    data = [CategoryPeriodAmount(
        standardized_category=r["standardized_category"],
        period=r["period"],
        amount=r["amount"],
    ) for r in rows]

    periods = sorted(set(r["period"] for r in rows))
    categories = sorted(set(r["standardized_category"] for r in rows))

    # Compute period summaries
    period_totals: dict[date, dict] = {}
    for r in rows:
        p = r["period"]
        if p not in period_totals:
            period_totals[p] = {"revenue": Decimal("0"), "costs": Decimal("0")}
        cat = r["standardized_category"]
        amt = r["amount"]
        if cat == "revenue":
            period_totals[p]["revenue"] += amt
        elif cat in ("material_costs", "personnel_costs", "other_operating_expenses"):
            period_totals[p]["costs"] += abs(amt)

    summaries = []
    for p in periods:
        t = period_totals.get(p, {"revenue": Decimal("0"), "costs": Decimal("0")})
        summaries.append(PeriodSummary(
            period=p,
            total_revenue=t["revenue"],
            total_costs=t["costs"],
            ebitda=t["revenue"] - t["costs"],
        ))

    return FinancialSummaryResponse(
        periods=periods, categories=categories, data=data, period_summaries=summaries,
    )


@router.get("/data/periods", response_model=list[date])
async def list_periods(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await db.execute(
        select(func.distinct(FinancialLineItem.period))
        .where(FinancialLineItem.project_id == project_id)
        .order_by(FinancialLineItem.period.desc())
    )
    return [row[0] for row in result.all()]


# --- Analysis ---

@router.post("/analysis/run", status_code=202)
async def trigger_analysis(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)
    background_tasks.add_task(_run_analysis_task, project_id)
    return {"message": "Variance analysis started"}


async def _run_analysis_task(project_id: UUID):
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await run_variance_analysis(project_id, db)
        except Exception as e:
            logger.exception("Variance analysis failed for project %s: %s", project_id, e)


@router.get("/analysis/internal", response_model=list[VarianceResultResponse])
async def get_internal_variance(
    project_id: UUID,
    analysis_type: str | None = Query(None, pattern="^(mom|yoy)$"),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    query = select(VarianceResult).where(VarianceResult.project_id == project_id)
    if analysis_type:
        query = query.where(VarianceResult.analysis_type == analysis_type)
    if category:
        query = query.where(VarianceResult.standardized_category == category)
    query = query.order_by(VarianceResult.significance.desc(), VarianceResult.period.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/analysis/external", response_model=list[BenchmarkComparison])
async def get_external_benchmarks(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    project = await check_project_access(project_id, user, db)
    industry = project.industry or ""
    if not industry:
        return []
    return await compute_benchmarks(project_id, industry, db)


@router.get("/analysis/trends/{category}", response_model=TrendResponse)
async def get_trend(
    project_id: UUID,
    category: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await compute_trend(project_id, category, db)
    return result


# --- Queries (HITL) ---

@router.get("/queries", response_model=list[FinanceQueryResponse])
async def list_queries(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await db.execute(
        select(FinanceQuery)
        .where(FinanceQuery.project_id == project_id)
        .order_by(FinanceQuery.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/queries/{query_id}", response_model=FinanceQueryResponse)
async def review_query(
    project_id: UUID,
    query_id: UUID,
    data: QueryReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)
    query = await db.get(FinanceQuery, query_id)
    if not query or query.project_id != project_id:
        raise HTTPException(status_code=404, detail="Query not found")

    if data.status not in (FinanceQueryStatus.approved, FinanceQueryStatus.rejected):
        raise HTTPException(status_code=422, detail="Status must be approved or rejected")

    query.status = data.status
    query.approved_by = user.id
    query.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(query)
    return query
