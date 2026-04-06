"""
Finance Module — API endpoints for financial data import, mapping, and variance analysis.

Tech: FastAPI + pandas + openpyxl + numpy + Groq API
Includes: SKR03/SKR04 detection (spec §9.1), German number parsing
"""
import io
import re
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from modules.auth.dependencies import project_manager, project_contributor, project_reader
from modules.auth.models import User
from .models import FinancialDataset, FinancialLineItem, VarianceAnalysis, FinancialInsight, ChartOfAccounts
from .schemas import FinancialDatasetOut, LineItemOut, VarianceAnalysisOut, FinancialInsightOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects/{project_id}/finance", tags=["finance"])


# ── German Number Parsing ──────────────────────────────────
# German format: 1.234,56 → English: 1234.56
# Handles: "1.234,56" / "1234,56" / "-1.234,56" / "(1.234,56)"

def parse_german_number(value) -> float | None:
    """
    Parse a number that may be in German format (dot=thousands, comma=decimal).
    Returns float or None if not parseable.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if not s:
        return None

    # Handle parenthetical negatives: (1.234,56) → -1234.56
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
        is_negative = True
    if s.startswith("-"):
        s = s[1:].strip()
        is_negative = True

    # Remove currency symbols and whitespace
    s = re.sub(r'[€$£\s]', '', s)

    if not s:
        return None

    # Detect German format: has dots as thousands separators AND comma as decimal
    # German: "1.234,56" or "1.234.567,89"
    # English: "1,234.56" or "1,234,567.89"
    has_comma = ',' in s
    has_dot = '.' in s

    if has_comma and has_dot:
        # Both present — determine which is decimal separator
        last_comma = s.rfind(',')
        last_dot = s.rfind('.')
        if last_comma > last_dot:
            # German: dots are thousands, comma is decimal → "1.234,56"
            s = s.replace('.', '').replace(',', '.')
        else:
            # English: commas are thousands, dot is decimal → "1,234.56"
            s = s.replace(',', '')
    elif has_comma and not has_dot:
        # Only comma — could be German decimal ("1234,56") or English thousands ("1,234")
        # Heuristic: if exactly 2 digits after comma, treat as German decimal
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(',', '.')
        else:
            # Multiple commas or >2 digits after → thousands separator
            s = s.replace(',', '')
    # If only dots, leave as-is (standard English)

    try:
        result = float(s)
        return -result if is_negative else result
    except ValueError:
        return None


def parse_german_numbers_in_df(df):
    """Apply German number parsing to all columns of a DataFrame."""
    import pandas as pd

    for col in df.columns:
        # Skip columns that are already numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            continue

        # Try parsing string columns as German numbers
        sample = df[col].dropna().head(10)
        if sample.empty:
            continue

        parsed = sample.apply(parse_german_number)
        success_rate = parsed.notna().sum() / len(parsed) if len(parsed) > 0 else 0

        if success_rate >= 0.5:
            df[col] = df[col].apply(parse_german_number)

    return df


# ── SKR03/SKR04 Detection ──────────────────────────────────
# Per spec §9.1: Automatic account mapping (SKR03/SKR04 chart of accounts detection)

# Common SKR03 account number ranges
SKR03_ACCOUNTS = {
    "0": "Anlagevermögen",           # Fixed assets
    "1": "Umlaufvermögen/Geldkonten",  # Current assets / cash
    "2": "Eigenkapital/Rückstellungen", # Equity / provisions
    "3": "Verbindlichkeiten",          # Liabilities
    "4": "Erlöse",                     # Revenue
    "5": "Materialaufwand",            # Material costs (COGS)
    "6": "Personalaufwand",            # Personnel costs
    "7": "Abschreibungen/sonstiger Aufwand", # Depreciation / other costs
    "8": "Erträge",                    # Income (financial)
    "9": "Vortrags/Statistikkonten",   # Carry-forward / statistical
}

# Signature accounts unique to SKR03
SKR03_SIGNATURES = {
    "1200": "Bank",
    "1000": "Kasse",
    "1400": "Forderungen aus L+L",
    "1600": "Verbindlichkeiten aus L+L",
    "4400": "Erlöse 19%",
    "3400": "Wareneingang 19%",
    "6000": "Löhne",
    "6300": "Gehälter",
}

# Signature accounts unique to SKR04
SKR04_SIGNATURES = {
    "1800": "Bank",
    "1600": "Kasse",
    "1200": "Forderungen aus L+L",
    "3300": "Verbindlichkeiten aus L+L",
    "4400": "Umsatzerlöse 19%",
    "5000": "Materialaufwand",
    "6000": "Aufwendungen für Löhne",
    "6300": "Aufwendungen für Gehälter",
}


def detect_chart_of_accounts(raw_data: list[dict], columns: list[str]) -> ChartOfAccounts | None:
    """
    Detect whether uploaded data uses SKR03 or SKR04 chart of accounts.
    Analyzes account numbers against known signature patterns.
    """
    # Find the column most likely to contain account numbers
    acct_col = None
    for col in columns:
        col_lower = col.lower().strip()
        if any(kw in col_lower for kw in ["konto", "account", "kontonr", "acct", "kto"]):
            acct_col = col
            break

    # If no explicit account column, look for columns with 4-digit numbers
    if not acct_col:
        for col in columns:
            values = [str(row.get(col, "")).strip() for row in raw_data[:50] if row.get(col)]
            four_digit_count = sum(1 for v in values if re.match(r'^\d{4}$', v))
            if four_digit_count >= 3:
                acct_col = col
                break

    if not acct_col:
        return None

    # Extract account numbers from the data
    account_numbers = set()
    for row in raw_data:
        val = str(row.get(acct_col, "")).strip()
        # Extract 4-digit account number
        match = re.match(r'^(\d{4})', val)
        if match:
            account_numbers.add(match.group(1))

    if not account_numbers:
        return None

    # Score against SKR03 and SKR04 signatures
    skr03_score = sum(1 for acct in account_numbers if acct in SKR03_SIGNATURES)
    skr04_score = sum(1 for acct in account_numbers if acct in SKR04_SIGNATURES)

    # Additional heuristic: check account number ranges
    # SKR03: Revenue in 4xxx, COGS in 3xxx/5xxx
    # SKR04: Revenue in 4xxx, Material in 5xxx, Personnel in 6xxx
    for acct in account_numbers:
        prefix = acct[0]
        if prefix == "1" and acct in ("1800",):
            skr04_score += 1
        elif prefix == "1" and acct in ("1200",):
            skr03_score += 1
        elif prefix == "5" and int(acct) >= 5000:
            skr04_score += 0.5
        elif prefix == "3" and int(acct) >= 3400:
            skr03_score += 0.5

    if skr03_score > skr04_score and skr03_score >= 2:
        return ChartOfAccounts.skr03
    elif skr04_score > skr03_score and skr04_score >= 2:
        return ChartOfAccounts.skr04
    elif skr03_score > 0 or skr04_score > 0:
        return ChartOfAccounts.skr03 if skr03_score >= skr04_score else ChartOfAccounts.skr04

    return ChartOfAccounts.custom


# ── File Parsing ───────────────────────────────────────────

def _parse_financial_file(file_bytes: bytes, filename: str) -> list[dict]:
    """Parse Excel/CSV/TSV file with German number support and return list of row dicts."""
    import pandas as pd

    ext = filename.rsplit(".", 1)[-1].lower()
    try:
        if ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl" if ext == "xlsx" else None)
        elif ext == "csv":
            # Try semicolon separator first (common in German CSV)
            content = file_bytes.decode("utf-8", errors="replace")
            if content.count(";") > content.count(","):
                df = pd.read_csv(io.BytesIO(file_bytes), sep=";", encoding="utf-8")
            else:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
        elif ext == "tsv":
            df = pd.read_csv(io.BytesIO(file_bytes), sep="\t", encoding="utf-8")
        else:
            return []

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]

        # Apply German number parsing to all columns
        df = parse_german_numbers_in_df(df)

        # Convert to list of dicts, handling NaN
        records = df.where(df.notna(), None).to_dict(orient="records")
        return records
    except Exception as e:
        logger.warning("Failed to parse financial file %s: %s", filename, e)
        return []


# ── Endpoints ──────────────────────────────────────────────

@router.post("/upload", response_model=FinancialDatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_financial_data(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_contributor),
):
    """Import financial data from Excel (.xlsx) or CSV/TSV file with SKR detection."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xls", "tsv", "csv"):
        raise HTTPException(status_code=400, detail="Supported formats: .xlsx, .xls, .tsv, .csv")

    file_bytes = await file.read()

    # Parse the file with German number support
    raw_data = _parse_financial_file(file_bytes, file.filename)

    # Detect chart of accounts (SKR03/SKR04)
    detected_chart = None
    columns = list(raw_data[0].keys()) if raw_data else []
    if raw_data:
        detected_chart = detect_chart_of_accounts(raw_data, columns)

    dataset = FinancialDataset(
        project_id=project_id,
        uploaded_by=user.id,
        name=file.filename,
        source_filename=file.filename,
        chart_of_accounts=detected_chart,
        raw_data=raw_data if raw_data else None,
        structure_metadata={
            "row_count": len(raw_data),
            "columns": columns,
            "detected_chart": detected_chart.value if detected_chart else None,
        },
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=list[FinancialDatasetOut])
async def list_datasets(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
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
    user: User = Depends(project_reader),
):
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
    user: User = Depends(project_reader),
):
    result = await db.execute(
        select(VarianceAnalysis)
        .where(VarianceAnalysis.project_id == project_id)
        .order_by(VarianceAnalysis.created_at.desc())
    )
    return list(result.scalars().all())


async def _run_variance(project_id: UUID, analysis_type: str, db: AsyncSession) -> list[dict]:
    """Compute variance analysis from uploaded datasets."""
    result = await db.execute(
        select(FinancialDataset)
        .where(FinancialDataset.project_id == project_id)
        .where(FinancialDataset.raw_data.isnot(None))
        .order_by(FinancialDataset.created_at.desc())
    )
    datasets = list(result.scalars().all())

    if not datasets:
        return []

    try:
        import pandas as pd

        all_rows = []
        for ds in datasets:
            if ds.raw_data:
                all_rows.extend(ds.raw_data)

        if not all_rows:
            return []

        df = pd.DataFrame(all_rows)
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if not numeric_cols:
            return []

        results = []
        for col in numeric_cols[:10]:
            series = df[col].dropna()
            if len(series) < 2:
                continue

            mean_val = float(series.mean())
            std_val = float(series.std())

            variance_pct = round((std_val / abs(mean_val) * 100), 1) if mean_val != 0 else 0
            flag = "significant" if variance_pct > 20 else "normal"

            results.append({
                "metric": str(col),
                "current": round(float(series.iloc[-1]), 2),
                "prior": round(float(series.iloc[0]), 2),
                "mean": round(mean_val, 2),
                "variance_pct": variance_pct,
                "flag": flag,
            })

        return results
    except Exception as e:
        logger.warning("Variance computation failed: %s", e)
        return []



@router.post("/variance/run", response_model=VarianceAnalysisOut, status_code=status.HTTP_201_CREATED)
async def run_variance_analysis(
    project_id: UUID,
    analysis_type: str = "internal_historical",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    # Check for uploaded datasets
    ds_result = await db.execute(
        select(FinancialDataset).where(FinancialDataset.project_id == project_id).limit(1)
    )
    has_datasets = ds_result.scalar_one_or_none() is not None

    # Also check for AI insights with variance data
    insight_result = await db.execute(
        select(FinancialInsight)
        .where(FinancialInsight.project_id == project_id)
        .where(FinancialInsight.status == "completed")
        .order_by(FinancialInsight.created_at.desc())
        .limit(1)
    )
    latest_insight = insight_result.scalar_one_or_none()

    if not has_datasets and not latest_insight:
        raise HTTPException(
            status_code=400,
            detail="Upload financial data or run AI analysis on data room documents first.",
        )

    # Try dataset-based variance first
    results = await _run_variance(project_id, analysis_type, db)

    # Fall back to AI insight variance if no dataset results
    if not results and latest_insight and latest_insight.variance_results:
        results = latest_insight.variance_results

    analysis = VarianceAnalysis(
        project_id=project_id,
        analysis_type=analysis_type,
        results=results,
        generated_queries=_generate_follow_up_queries(results),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


def _generate_follow_up_queries(results: list[dict]) -> list[dict]:
    queries = []
    for r in results:
        if r.get("flag") == "significant":
            metric = r.get("metric", "Unknown")
            variance = r.get("variance_pct", 0)
            direction = "increase" if variance > 0 else "decrease"
            queries.append({
                "question": f"Explain the {abs(variance)}% {direction} in {metric} — what are the primary drivers?",
                "metric": metric,
                "priority": "high",
            })
    return queries


# ── Financial KPIs ────────────────────────────────────────

def _compute_kpis(raw_data: list[dict], columns: list[str]) -> list[dict]:
    """Compute financial KPIs from raw uploaded data."""
    import pandas as pd

    if not raw_data:
        return []

    df = pd.DataFrame(raw_data)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        return []

    kpis = []
    # Sum numeric columns to derive totals
    totals = {col: float(df[col].dropna().sum()) for col in numeric_cols}

    # Try to identify key financial line items by column name
    revenue_keys = [c for c in numeric_cols if any(k in c.lower() for k in ["revenue", "umsatz", "erlös", "sales"])]
    cogs_keys = [c for c in numeric_cols if any(k in c.lower() for k in ["cogs", "cost of goods", "materialaufwand", "wareneinsatz"])]
    opex_keys = [c for c in numeric_cols if any(k in c.lower() for k in ["opex", "operating", "betriebsaufwand", "verwaltung"])]
    personnel_keys = [c for c in numeric_cols if any(k in c.lower() for k in ["personnel", "personal", "löhne", "gehälter", "salary", "wages"])]

    revenue = sum(totals.get(k, 0) for k in revenue_keys) if revenue_keys else None
    cogs = sum(totals.get(k, 0) for k in cogs_keys) if cogs_keys else None
    opex = sum(totals.get(k, 0) for k in opex_keys) if opex_keys else None
    personnel = sum(totals.get(k, 0) for k in personnel_keys) if personnel_keys else None

    if revenue and revenue != 0:
        gross_profit = (revenue - cogs) if cogs is not None else None
        ebitda = (gross_profit - opex) if gross_profit is not None and opex is not None else None

        kpis.append({"name": "Revenue", "value": round(revenue, 2), "unit": "EUR", "category": "earnings"})
        if gross_profit is not None:
            kpis.append({"name": "Gross Profit", "value": round(gross_profit, 2), "unit": "EUR", "category": "earnings"})
            kpis.append({"name": "Gross Margin", "value": round(gross_profit / revenue * 100, 1), "unit": "%", "category": "profitability"})
        if ebitda is not None:
            kpis.append({"name": "EBITDA", "value": round(ebitda, 2), "unit": "EUR", "category": "earnings"})
            kpis.append({"name": "EBITDA Margin", "value": round(ebitda / revenue * 100, 1), "unit": "%", "category": "profitability"})
        if personnel is not None:
            kpis.append({"name": "Personnel Cost Ratio", "value": round(personnel / revenue * 100, 1), "unit": "%", "category": "efficiency"})
        if cogs is not None:
            kpis.append({"name": "Cost of Goods Sold", "value": round(cogs, 2), "unit": "EUR", "category": "earnings"})
            kpis.append({"name": "Material Cost Ratio", "value": round(cogs / revenue * 100, 1), "unit": "%", "category": "efficiency"})

    return kpis



@router.get("/kpis")
async def get_financial_kpis(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """Get computed financial KPIs for the project (spec §12.3).
    Uses uploaded datasets first; falls back to latest AI insight if no datasets."""
    # 1. Try from uploaded datasets
    result = await db.execute(
        select(FinancialDataset)
        .where(FinancialDataset.project_id == project_id)
        .where(FinancialDataset.raw_data.isnot(None))
        .order_by(FinancialDataset.created_at.desc())
    )
    datasets = list(result.scalars().all())

    all_rows = []
    columns: list[str] = []
    for ds in datasets:
        if ds.raw_data:
            all_rows.extend(ds.raw_data)
            if not columns and ds.structure_metadata:
                columns = ds.structure_metadata.get("columns", [])

    kpis = _compute_kpis(all_rows, columns)
    if kpis:
        return kpis

    # 2. Fall back to latest AI insight
    insight_result = await db.execute(
        select(FinancialInsight)
        .where(FinancialInsight.project_id == project_id)
        .where(FinancialInsight.status == "completed")
        .order_by(FinancialInsight.created_at.desc())
        .limit(1)
    )
    insight = insight_result.scalar_one_or_none()
    if insight and insight.kpis:
        return insight.kpis

    return []


# ── Period Comparison ─────────────────────────────────────

@router.get("/period-comparison")
async def get_period_comparison(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """Multi-period comparison — compares metrics across all uploaded datasets (spec §9.3)."""
    result = await db.execute(
        select(FinancialDataset)
        .where(FinancialDataset.project_id == project_id)
        .where(FinancialDataset.raw_data.isnot(None))
        .order_by(FinancialDataset.created_at.asc())
    )
    datasets = list(result.scalars().all())

    if not datasets:
        return []

    try:
        import pandas as pd

        periods = []
        for ds in datasets:
            if not ds.raw_data:
                continue
            df = pd.DataFrame(ds.raw_data)
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if not numeric_cols:
                continue

            period_label = ds.name or ds.source_filename
            if ds.period_from:
                period_label = str(ds.period_from)

            period_data = {"period": period_label, "dataset_id": str(ds.id)}
            for col in numeric_cols[:10]:
                series = df[col].dropna()
                if len(series) > 0:
                    period_data[col] = round(float(series.sum()), 2)
            periods.append(period_data)

        if len(periods) < 2:
            return []

        # Build comparison with variance between consecutive periods
        comparisons = []
        metric_names = [k for k in periods[0].keys() if k not in ("period", "dataset_id")]
        for metric in metric_names:
            row = {"metric": metric, "periods": []}
            for i, p in enumerate(periods):
                entry = {"period": p["period"], "value": p.get(metric, 0)}
                if i > 0:
                    prev_val = periods[i - 1].get(metric, 0)
                    curr_val = p.get(metric, 0)
                    if prev_val and prev_val != 0:
                        entry["change_pct"] = round((curr_val - prev_val) / abs(prev_val) * 100, 1)
                    else:
                        entry["change_pct"] = 0
                row["periods"].append(entry)
            comparisons.append(row)

        return comparisons
    except Exception as e:
        logger.warning("Period comparison failed: %s", e)
        return []



# ── AI Document Analysis ─────────────────────────────────

@router.post("/analyze", response_model=FinancialInsightOut, status_code=status.HTTP_201_CREATED)
async def analyze_financial_data(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """
    AI-powered financial analysis: pulls documents from the data room + uploaded
    datasets, extracts figures, computes KPIs, finds variance, and generates
    follow-up questions for anomalies.
    """
    from .analyzer import run_financial_analysis
    insight = await run_financial_analysis(project_id, user.id, db)
    if insight.status == "failed" and not insight.extracted_figures:
        raise HTTPException(
            status_code=400,
            detail=insight.summary or "Analysis failed. Ensure financial documents or datasets are available.",
        )
    return insight


@router.get("/insights", response_model=list[FinancialInsightOut])
async def list_insights(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """List all AI-generated financial insights for the project, newest first."""
    result = await db.execute(
        select(FinancialInsight)
        .where(FinancialInsight.project_id == project_id)
        .order_by(FinancialInsight.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/insights/latest", response_model=FinancialInsightOut)
async def get_latest_insight(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """Get the most recent completed AI financial insight."""
    result = await db.execute(
        select(FinancialInsight)
        .where(FinancialInsight.project_id == project_id)
        .where(FinancialInsight.status == "completed")
        .order_by(FinancialInsight.created_at.desc())
        .limit(1)
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="No completed analysis found. Run an analysis first.")
    return insight


# ── Chart Data ────────────────────────────────────────────

@router.get("/chart-data")
async def get_chart_data(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """Pre-processed chart data for frontend visualization (spec §12.3)."""
    result = await db.execute(
        select(VarianceAnalysis)
        .where(VarianceAnalysis.project_id == project_id)
        .order_by(VarianceAnalysis.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    variance_chart = []
    if latest and latest.results:
        for r in latest.results:
            variance_chart.append({
                "name": r.get("metric", ""),
                "current": r.get("current", 0),
                "prior": r.get("prior", 0),
                "variance_pct": r.get("variance_pct", 0),
                "flag": r.get("flag", "normal"),
            })

    # Fall back to AI insight variance data if no manual variance analysis exists
    if not variance_chart:
        insight_result = await db.execute(
            select(FinancialInsight)
            .where(FinancialInsight.project_id == project_id)
            .where(FinancialInsight.status == "completed")
            .order_by(FinancialInsight.created_at.desc())
            .limit(1)
        )
        ai_insight = insight_result.scalar_one_or_none()
        if ai_insight and ai_insight.variance_results:
            for r in ai_insight.variance_results:
                variance_chart.append({
                    "name": r.get("metric", ""),
                    "current": r.get("current", 0),
                    "prior": r.get("prior", 0),
                    "variance_pct": r.get("variance_pct", 0),
                    "flag": r.get("flag", "normal"),
                })

    # Period comparison data for trend chart
    period_data = await get_period_comparison(project_id, db, user)

    return {
        "variance": variance_chart,
        "trends": period_data,
    }
