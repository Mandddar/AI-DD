"""
Variance analysis engine — MoM, YoY, trends, benchmarks, query generation.
All heavy calculations run in SQL for performance.
"""
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text, select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    FinancialLineItem, VarianceResult, BenchmarkData, FinanceQuery,
    AnalysisType, VarianceSignificance, FinanceQueryStatus,
)

logger = logging.getLogger(__name__)


def classify_significance(variance_pct: float | None, variance_abs: Decimal | None) -> VarianceSignificance:
    """Classify variance significance based on thresholds for SME deals."""
    if variance_pct is None and variance_abs is None:
        return VarianceSignificance.normal
    abs_pct = abs(variance_pct) if variance_pct else 0
    abs_val = abs(float(variance_abs)) if variance_abs else 0
    if abs_pct > 50 or abs_val > 500_000:
        return VarianceSignificance.critical
    if abs_pct > 25 or abs_val > 100_000:
        return VarianceSignificance.significant
    if abs_pct > 10 or abs_val > 25_000:
        return VarianceSignificance.notable
    return VarianceSignificance.normal


# --- Query generation templates ---

QUERY_TEMPLATES = {
    "revenue": "Revenue {direction} by {pct}% ({abs_formatted}) in {period}. Please explain the drivers: new/lost customers, pricing changes, one-off items, or seasonal factors.",
    "personnel_costs": "Personnel costs {direction} by {pct}% ({abs_formatted}) in {period}. Please detail: (a) headcount changes, (b) salary adjustments, (c) severance or one-off payments, (d) contractor costs.",
    "material_costs": "Material/COGS costs {direction} by {pct}% ({abs_formatted}) in {period}. Please explain: supplier price changes, volume effects, inventory adjustments, or one-off purchases.",
    "other_operating_expenses": "Other operating expenses {direction} by {pct}% ({abs_formatted}) in {period}. Please break down: consulting fees, marketing spend, rent changes, or extraordinary items.",
    "depreciation": "Depreciation/amortization {direction} by {pct}% ({abs_formatted}) in {period}. Please explain: asset acquisitions, disposals, impairments, or changes in useful life estimates.",
    "default": "{category} {direction} by {pct}% ({abs_formatted}) in {period}. Please provide a detailed explanation of the drivers behind this change.",
}


def generate_query_text(variance: VarianceResult) -> str:
    """Generate a follow-up query from a variance result."""
    category = variance.standardized_category or "general"
    template = QUERY_TEMPLATES.get(category, QUERY_TEMPLATES["default"])

    pct = round(abs(variance.variance_pct), 1) if variance.variance_pct else 0
    direction = "increased" if (variance.variance_pct or 0) > 0 else "decreased"
    abs_val = abs(float(variance.variance_abs)) if variance.variance_abs else 0
    abs_formatted = f"EUR {abs_val:,.0f}"
    period_str = variance.period.strftime("%B %Y")

    return template.format(
        pct=pct, direction=direction, abs_formatted=abs_formatted,
        period=period_str, category=category.replace("_", " ").title(),
    )


async def run_variance_analysis(project_id: UUID, db: AsyncSession) -> None:
    """Run full variance analysis for a project. Clears previous results and recomputes."""

    # Clear previous results
    await db.execute(delete(FinanceQuery).where(
        FinanceQuery.project_id == project_id,
        FinanceQuery.status == FinanceQueryStatus.pending_review,
    ))
    await db.execute(delete(VarianceResult).where(VarianceResult.project_id == project_id))
    await db.flush()

    # Get available periods
    periods_result = await db.execute(
        select(func.distinct(FinancialLineItem.period))
        .where(FinancialLineItem.project_id == project_id)
        .order_by(FinancialLineItem.period.desc())
    )
    periods = [row[0] for row in periods_result.all()]
    if len(periods) < 2:
        logger.info("Project %s has fewer than 2 periods — skipping variance analysis", project_id)
        return

    latest_period = periods[0]

    # --- MoM Analysis ---
    prior_month = latest_period - relativedelta(months=1)
    await _compute_comparison(db, project_id, latest_period, prior_month, AnalysisType.mom)

    # --- YoY Analysis ---
    same_month_prior_year = latest_period - relativedelta(years=1)
    if same_month_prior_year in periods:
        await _compute_comparison(db, project_id, latest_period, same_month_prior_year, AnalysisType.yoy)

    await db.commit()

    # --- Generate queries for significant/critical variances ---
    sig_results = await db.execute(
        select(VarianceResult).where(
            VarianceResult.project_id == project_id,
            VarianceResult.significance.in_([
                VarianceSignificance.significant,
                VarianceSignificance.critical,
            ]),
        )
    )
    for vr in sig_results.scalars().all():
        query_text = generate_query_text(vr)
        context = f"{vr.analysis_type.value.upper()} variance: {vr.standardized_category} changed by {vr.variance_pct:.1f}%"
        db.add(FinanceQuery(
            project_id=project_id,
            variance_id=vr.id,
            question=query_text,
            context=context,
        ))

    await db.commit()


async def _compute_comparison(
    db: AsyncSession,
    project_id: UUID,
    current_period: date,
    comparison_period: date,
    analysis_type: AnalysisType,
) -> None:
    """Compute variance between two periods for all categories."""
    result = await db.execute(text("""
        WITH current AS (
            SELECT standardized_category, SUM(amount) AS amount
            FROM financial_line_items
            WHERE project_id = :pid AND period = :current_period AND standardized_category IS NOT NULL
            GROUP BY standardized_category
        ),
        comparison AS (
            SELECT standardized_category, SUM(amount) AS amount
            FROM financial_line_items
            WHERE project_id = :pid AND period = :comparison_period AND standardized_category IS NOT NULL
            GROUP BY standardized_category
        )
        SELECT
            COALESCE(c.standardized_category, p.standardized_category) AS category,
            COALESCE(c.amount, 0) AS current_amount,
            COALESCE(p.amount, 0) AS prior_amount,
            COALESCE(c.amount, 0) - COALESCE(p.amount, 0) AS variance_abs,
            CASE WHEN COALESCE(p.amount, 0) != 0
                 THEN ((COALESCE(c.amount, 0) - p.amount) / ABS(p.amount)) * 100
                 ELSE NULL
            END AS variance_pct
        FROM current c
        FULL OUTER JOIN comparison p USING (standardized_category)
    """).bindparams(
        pid=project_id,
        current_period=current_period,
        comparison_period=comparison_period,
    ))

    for row in result.mappings().all():
        significance = classify_significance(row["variance_pct"], row["variance_abs"])
        db.add(VarianceResult(
            project_id=project_id,
            analysis_type=analysis_type,
            standardized_category=row["category"],
            period=current_period,
            comparison_period=comparison_period,
            variance_pct=row["variance_pct"],
            variance_abs=row["variance_abs"],
            significance=significance,
        ))


async def compute_trend(
    project_id: UUID,
    category: str,
    db: AsyncSession,
) -> dict:
    """Compute trend data for a specific category."""
    result = await db.execute(
        select(FinancialLineItem.period, func.sum(FinancialLineItem.amount).label("amount"))
        .where(
            FinancialLineItem.project_id == project_id,
            FinancialLineItem.standardized_category == category,
        )
        .group_by(FinancialLineItem.period)
        .order_by(FinancialLineItem.period)
    )
    rows = result.all()
    if len(rows) < 2:
        return {"category": category, "direction": "stable", "avg_growth_rate": None, "data_points": []}

    data_points = [{"period": r.period, "amount": r.amount} for r in rows]

    # Compute average growth rate
    amounts = [float(r.amount) for r in rows]
    growth_rates = []
    for i in range(1, len(amounts)):
        if amounts[i - 1] != 0:
            rate = ((amounts[i] - amounts[i - 1]) / abs(amounts[i - 1])) * 100
            growth_rates.append(rate)

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0

    if avg_growth > 5:
        direction = "growing"
    elif avg_growth < -5:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "category": category,
        "direction": direction,
        "avg_growth_rate": round(avg_growth, 2),
        "data_points": data_points,
    }


async def compute_benchmarks(
    project_id: UUID,
    industry: str,
    db: AsyncSession,
) -> list[dict]:
    """Compare company metrics against industry benchmarks."""
    # Compute company metrics from line items
    result = await db.execute(text("""
        SELECT
            standardized_category,
            SUM(amount) AS total
        FROM financial_line_items
        WHERE project_id = :pid AND standardized_category IS NOT NULL
        GROUP BY standardized_category
    """).bindparams(pid=project_id))

    totals = {row["standardized_category"]: float(row["total"]) for row in result.mappings().all()}
    revenue = totals.get("revenue", 0)

    if revenue == 0:
        return []

    company_metrics = {}
    if "personnel_costs" in totals:
        company_metrics["personnel_cost_ratio"] = abs(totals["personnel_costs"]) / revenue * 100
    if "material_costs" in totals:
        ebitda = revenue - abs(totals.get("material_costs", 0)) - abs(totals.get("personnel_costs", 0)) - abs(totals.get("other_operating_expenses", 0))
        company_metrics["ebitda_margin"] = ebitda / revenue * 100

    # Get benchmarks
    bench_result = await db.execute(
        select(BenchmarkData).where(BenchmarkData.industry == industry)
    )
    benchmarks = list(bench_result.scalars().all())

    comparisons = []
    for b in benchmarks:
        if b.metric_name in company_metrics:
            comparisons.append({
                "metric_name": b.metric_name,
                "company_value": round(company_metrics[b.metric_name], 2),
                "industry_value": b.metric_value,
                "delta": round(company_metrics[b.metric_name] - b.metric_value, 2),
                "source": b.source,
                "year": b.year,
            })

    return comparisons
