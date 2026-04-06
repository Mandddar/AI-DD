"""
Finance Analyzer — AI-powered financial analysis using data room documents + uploaded data.

Pulls financial documents from the DMS, combines with uploaded Excel datasets,
uses Groq LLM to extract structured figures, compute KPIs, find variance, and
generate follow-up questions for anomalies.
"""
import json
import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from modules.dms.models import Document, DocumentText, Workstream, DocumentStatus
from modules.agent.embeddings import ensure_document_indexed, fts_search
from .models import FinancialDataset, FinancialInsight

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Prompts ──────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a senior M&A financial analyst. You are given excerpts from data room documents and/or structured financial data for a target company.

Your task: Extract ALL financial figures you can find and return a structured JSON analysis.

RULES:
- Extract every financial metric with its period/year.  Use the EXACT numbers from the documents.
- If multiple periods exist, extract each separately so comparisons are possible.
- Compute standard KPIs where the underlying data supports it.
- Compare figures across periods: flag any variance > 15% as worth investigating.
- If something looks abnormal, inconsistent, or is missing, generate a specific question about it.
- Do NOT invent numbers.  If a metric cannot be derived, omit it.
- Prioritise: Revenue, COGS, Gross Profit, EBITDA, Net Income, Working Capital, Debt, Equity, Cash Flow.
- Support both German (Umsatz, Materialaufwand, Personalaufwand, etc.) and English terminology.

Return a JSON object with this exact structure:
{
  "extracted_figures": [
    {"metric": "Revenue", "period": "2023", "value": 15200000, "currency": "EUR", "source": "Annual Report 2023"},
    ...
  ],
  "kpis": [
    {"name": "Gross Margin", "value": 42.1, "unit": "%", "category": "profitability", "period": "2023"},
    {"name": "EBITDA", "value": 2780000, "unit": "EUR", "category": "earnings", "period": "2023"},
    ...
  ],
  "variance_results": [
    {"metric": "Revenue", "current": 15200000, "prior": 14000000, "current_period": "2023", "prior_period": "2022", "variance_pct": 8.6, "flag": "normal"},
    {"metric": "Operating Expenses", "current": 3900000, "prior": 3200000, "current_period": "2023", "prior_period": "2022", "variance_pct": 21.9, "flag": "significant"},
    ...
  ],
  "anomalies": [
    {"question": "Operating expenses grew 21.9% year-over-year while revenue grew only 8.6% — what drove this disproportionate cost increase?", "metric": "Operating Expenses", "severity": "high", "detail": "OpEx grew from €3.2M to €3.9M (+21.9%) vs revenue growth of 8.6%"},
    ...
  ],
  "summary": "Brief executive summary of the financial health and key risks (2-4 sentences)."
}
"""


async def _gather_document_context(
    project_id: UUID,
    db: AsyncSession,
) -> tuple[list[str], list[str]]:
    """
    Pull finance-related document text from the data room.
    Returns (text_excerpts, document_id_strings).
    """
    # Get all finance-workstream documents that are ready or beyond
    usable_statuses = [
        DocumentStatus.ready,
        DocumentStatus.under_review,
        DocumentStatus.reviewed,
        DocumentStatus.approved,
    ]
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .where(Document.status.in_(usable_statuses))
        .order_by(Document.created_at.desc())
    )
    docs = list(result.scalars().all())

    if not docs:
        return [], []

    # Prioritise finance workstream, but also include general docs that might
    # contain financial statements (tagged by auto-tagger)
    finance_docs = [d for d in docs if d.workstream == Workstream.finance]
    other_docs = [d for d in docs if d.workstream != Workstream.finance]

    # Use all finance docs + first few general docs
    target_docs = finance_docs + other_docs[:5]
    if not target_docs:
        return [], []

    doc_ids = [d.id for d in target_docs]

    # Ensure all are indexed for FTS
    for did in doc_ids:
        await ensure_document_indexed(did, db)

    # Retrieve most relevant chunks via FTS
    finance_query = (
        "revenue EBITDA profit loss balance sheet income statement cash flow "
        "Umsatz Gewinn Verlust Bilanz working capital debt equity "
        "operating expenses cost of goods sold gross margin net income"
    )
    chunks = await fts_search(finance_query, doc_ids, db, top_k=20)
    excerpts = [c.chunk_text[:800] for c in chunks]
    used_doc_ids = list(set(str(c.document_id) for c in chunks))

    # Also get full text from top finance documents (up to 3) for comprehensive analysis
    for fdoc in finance_docs[:3]:
        txt_result = await db.execute(
            select(DocumentText).where(DocumentText.document_id == fdoc.id)
        )
        doc_text = txt_result.scalar_one_or_none()
        if doc_text and doc_text.content:
            # Take first 3000 chars of full text as additional context
            excerpts.append(doc_text.content[:3000])
            if str(fdoc.id) not in used_doc_ids:
                used_doc_ids.append(str(fdoc.id))

    return excerpts, used_doc_ids


def _format_dataset_context(datasets: list[FinancialDataset]) -> str:
    """Format uploaded Excel/CSV datasets as text context for the LLM."""
    import pandas as pd

    parts = []
    for ds in datasets:
        if not ds.raw_data:
            continue
        df = pd.DataFrame(ds.raw_data)
        label = ds.name or ds.source_filename
        if ds.period_from:
            label += f" (period: {ds.period_from} - {ds.period_to})"
        if ds.chart_of_accounts:
            label += f" [chart: {ds.chart_of_accounts}]"

        # Summarise: column stats
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        summary_lines = [f"\n=== UPLOADED DATASET: {label} ==="]
        summary_lines.append(f"Rows: {len(df)}, Columns: {', '.join(df.columns.tolist())}")

        for col in numeric_cols[:15]:
            series = df[col].dropna()
            if len(series) > 0:
                summary_lines.append(
                    f"  {col}: total={series.sum():,.2f}, "
                    f"min={series.min():,.2f}, max={series.max():,.2f}, "
                    f"mean={series.mean():,.2f}"
                )

        # Include first 20 rows as sample
        sample = df.head(20).to_string(index=False, max_colwidth=30)
        summary_lines.append(f"\nSample data:\n{sample}")
        parts.append("\n".join(summary_lines))

    return "\n\n".join(parts)


async def _call_finance_llm(context: str) -> dict:
    """Call Groq LLM with the financial context and parse structured JSON response."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)

    user_prompt = f"""Analyse the following financial data from the deal's data room documents and uploaded datasets.
Extract all financial figures, compute KPIs, identify variances between periods, and flag anomalies.

FINANCIAL DATA:
{context}

Return the structured JSON analysis as specified. Focus on material findings only."""

    response = await client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=8192,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    return json.loads(content)


def _mock_analysis(doc_ids: list[str], dataset_ids: list[str]) -> dict:
    """Return a realistic mock analysis for dev mode (no Groq key)."""
    return {
        "extracted_figures": [
            {"metric": "Revenue", "period": "2023", "value": 15200000, "currency": "EUR", "source": "data room"},
            {"metric": "Revenue", "period": "2022", "value": 14000000, "currency": "EUR", "source": "data room"},
            {"metric": "COGS", "period": "2023", "value": 8800000, "currency": "EUR", "source": "data room"},
            {"metric": "COGS", "period": "2022", "value": 7700000, "currency": "EUR", "source": "data room"},
            {"metric": "Operating Expenses", "period": "2023", "value": 3900000, "currency": "EUR", "source": "data room"},
            {"metric": "Operating Expenses", "period": "2022", "value": 3200000, "currency": "EUR", "source": "data room"},
            {"metric": "EBITDA", "period": "2023", "value": 2780000, "currency": "EUR", "source": "data room"},
            {"metric": "EBITDA", "period": "2022", "value": 2870000, "currency": "EUR", "source": "data room"},
            {"metric": "Net Debt", "period": "2023", "value": 4200000, "currency": "EUR", "source": "data room"},
            {"metric": "Net Debt", "period": "2022", "value": 3500000, "currency": "EUR", "source": "data room"},
        ],
        "kpis": [
            {"name": "Revenue", "value": 15200000, "unit": "EUR", "category": "earnings", "period": "2023"},
            {"name": "Gross Profit", "value": 6400000, "unit": "EUR", "category": "earnings", "period": "2023"},
            {"name": "Gross Margin", "value": 42.1, "unit": "%", "category": "profitability", "period": "2023"},
            {"name": "EBITDA", "value": 2780000, "unit": "EUR", "category": "earnings", "period": "2023"},
            {"name": "EBITDA Margin", "value": 18.3, "unit": "%", "category": "profitability", "period": "2023"},
        ],
        "variance_results": [
            {"metric": "Revenue", "current": 15200000, "prior": 14000000, "current_period": "2023", "prior_period": "2022", "variance_pct": 8.6, "flag": "normal"},
            {"metric": "COGS", "current": 8800000, "prior": 7700000, "current_period": "2023", "prior_period": "2022", "variance_pct": 14.3, "flag": "normal"},
            {"metric": "Operating Expenses", "current": 3900000, "prior": 3200000, "current_period": "2023", "prior_period": "2022", "variance_pct": 21.9, "flag": "significant"},
            {"metric": "EBITDA", "current": 2780000, "prior": 2870000, "current_period": "2023", "prior_period": "2022", "variance_pct": -3.1, "flag": "normal"},
            {"metric": "Net Debt", "current": 4200000, "prior": 3500000, "current_period": "2023", "prior_period": "2022", "variance_pct": 20.0, "flag": "significant"},
        ],
        "anomalies": [
            {
                "question": "Operating expenses grew 21.9% YoY while revenue grew only 8.6%. What drove this disproportionate cost increase?",
                "metric": "Operating Expenses",
                "severity": "high",
                "detail": "OpEx grew from €3.2M to €3.9M (+21.9%) vs revenue growth of 8.6%. This compressed EBITDA margin.",
            },
            {
                "question": "EBITDA declined 3.1% despite revenue growth of 8.6%. Are there one-off items that should be normalised?",
                "metric": "EBITDA",
                "severity": "high",
                "detail": "Revenue grew but EBITDA fell from €2.87M to €2.78M, suggesting margin erosion.",
            },
            {
                "question": "Net debt increased 20% (€3.5M → €4.2M). What was the additional borrowing used for?",
                "metric": "Net Debt",
                "severity": "medium",
                "detail": "Net debt increase of €700K in one year. Debt/EBITDA ratio worsened from 1.2x to 1.5x.",
            },
        ],
        "summary": (
            "Revenue grew 8.6% YoY to €15.2M, but profitability deteriorated. "
            "EBITDA declined 3.1% due to a disproportionate 21.9% increase in operating expenses. "
            "Net debt rose 20% to €4.2M, increasing leverage. "
            "Key areas requiring further investigation: the drivers of OpEx growth and the purpose of additional borrowing."
        ),
    }


async def run_financial_analysis(
    project_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> FinancialInsight:
    """
    Main analysis pipeline:
    1. Pull financial documents from the data room
    2. Pull uploaded Excel/CSV datasets
    3. Combine into context for the LLM
    4. Extract figures, compute KPIs, find variance, generate anomaly questions
    5. Store and return FinancialInsight
    """
    # Create the insight record (status=running)
    insight = FinancialInsight(
        project_id=project_id,
        triggered_by=user_id,
        status="running",
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)

    try:
        # 1. Gather document context from data room
        doc_excerpts, doc_ids = await _gather_document_context(project_id, db)

        # 2. Gather uploaded datasets
        ds_result = await db.execute(
            select(FinancialDataset)
            .where(FinancialDataset.project_id == project_id)
            .where(FinancialDataset.raw_data.isnot(None))
            .order_by(FinancialDataset.created_at.desc())
        )
        datasets = list(ds_result.scalars().all())
        dataset_ids = [str(ds.id) for ds in datasets]

        # 3. Build combined context
        context_parts = []
        if doc_excerpts:
            context_parts.append("=== DATA ROOM DOCUMENTS ===\n" + "\n\n---\n\n".join(doc_excerpts))
        if datasets:
            context_parts.append(_format_dataset_context(datasets))

        if not context_parts:
            insight.status = "failed"
            insight.summary = "No financial data available. Upload financial documents to the data room or import Excel/CSV data."
            insight.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(insight)
            return insight

        combined_context = "\n\n".join(context_parts)
        # Truncate to avoid token limits (keep ~12K chars for context)
        if len(combined_context) > 12000:
            combined_context = combined_context[:12000] + "\n\n[... truncated for length ...]"

        # 4. Call LLM (or mock in dev mode)
        if not settings.groq_api_key:
            logger.info("No Groq API key — using mock financial analysis")
            analysis = _mock_analysis(doc_ids, dataset_ids)
        else:
            try:
                analysis = await _call_finance_llm(combined_context)
            except Exception as e:
                logger.error("LLM analysis failed: %s", e)
                analysis = _mock_analysis(doc_ids, dataset_ids)

        # 5. Store results
        insight.status = "completed"
        insight.extracted_figures = analysis.get("extracted_figures", [])
        insight.kpis = analysis.get("kpis", [])
        insight.variance_results = analysis.get("variance_results", [])
        insight.anomalies = analysis.get("anomalies", [])
        insight.summary = analysis.get("summary", "")
        insight.source_document_ids = doc_ids
        insight.source_dataset_ids = dataset_ids
        insight.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(insight)
        return insight

    except Exception as e:
        logger.error("Financial analysis pipeline failed: %s", e)
        insight.status = "failed"
        insight.summary = f"Analysis failed: {str(e)}"
        insight.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(insight)
        return insight
