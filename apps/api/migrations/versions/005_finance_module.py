"""Phase 4: Financial Analysis module — datasets, line items, account mappings, variance, benchmarks, queries.

Revision ID: 005_finance
Revises: 004_dms_phase2
Create Date: 2026-03-29
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005_finance"
down_revision: Union[str, None] = "004_dms_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enums ---
    chart_enum = sa.Enum("skr03", "skr04", "custom", name="chartofaccounts")
    dataset_status = sa.Enum("processing", "completed", "failed", name="datasetstatus")
    analysis_type = sa.Enum("mom", "yoy", "trend", "benchmark", name="analysistype")
    significance = sa.Enum("normal", "notable", "significant", "critical", name="variancesignificance")
    query_status = sa.Enum("pending_review", "approved", "rejected", name="financequerystatus")
    pnl_section = sa.Enum("revenue", "cost_of_goods", "personnel", "other_operating", "depreciation", "interest", "tax", "other", name="pnlsection")

    # --- financial_datasets ---
    op.create_table(
        "financial_datasets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("chart_of_accounts", chart_enum, nullable=False, server_default="custom"),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("imported_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("row_count", sa.Integer(), server_default="0"),
        sa.Column("status", dataset_status, nullable=False, server_default="processing"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- financial_line_items ---
    op.create_table(
        "financial_line_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("dataset_id", UUID(as_uuid=True), sa.ForeignKey("financial_datasets.id"), nullable=False),
        sa.Column("account_code", sa.String(20), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("standardized_category", sa.String(100), nullable=True),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "account_code", "period", name="uq_line_item_project_account_period"),
    )
    op.create_index("ix_line_items_project_period_category", "financial_line_items", ["project_id", "period", "standardized_category"])

    # --- account_mappings ---
    op.create_table(
        "account_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("chart_type", chart_enum, nullable=False),
        sa.Column("account_code_start", sa.String(10), nullable=False),
        sa.Column("account_code_end", sa.String(10), nullable=False),
        sa.Column("standardized_category", sa.String(100), nullable=False),
        sa.Column("display_name_de", sa.String(255), nullable=False),
        sa.Column("display_name_en", sa.String(255), nullable=False),
        sa.Column("is_revenue", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_cost", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pnl_section", pnl_section, nullable=False),
    )

    # --- Seed SKR03 mappings ---
    account_mappings = sa.table("account_mappings",
        sa.column("id", UUID), sa.column("chart_type", sa.String),
        sa.column("account_code_start", sa.String), sa.column("account_code_end", sa.String),
        sa.column("standardized_category", sa.String),
        sa.column("display_name_de", sa.String), sa.column("display_name_en", sa.String),
        sa.column("is_revenue", sa.Boolean), sa.column("is_cost", sa.Boolean),
        sa.column("pnl_section", sa.String),
    )

    skr03_data = [
        ("4000", "4999", "revenue", "Umsatzerlöse", "Revenue", True, False, "revenue"),
        ("5000", "5999", "material_costs", "Materialaufwand", "Material/COGS", False, True, "cost_of_goods"),
        ("6000", "6199", "personnel_costs", "Personalaufwand", "Personnel Costs", False, True, "personnel"),
        ("6200", "6599", "other_operating_expenses", "Sonstige betriebliche Aufwendungen", "Other Operating Expenses", False, True, "other_operating"),
        ("6600", "6699", "depreciation", "Abschreibungen", "Depreciation & Amortization", False, True, "depreciation"),
        ("6700", "6799", "interest_expense", "Zinsaufwand", "Interest Expense", False, True, "interest"),
        ("6800", "6899", "tax_expense", "Steuern", "Tax Expense", False, True, "tax"),
        ("6900", "6999", "extraordinary_items", "Außerordentliche Aufwendungen", "Extraordinary Items", False, True, "other"),
        ("7000", "7999", "other_income", "Sonstige betriebliche Erträge", "Other Operating Income", True, False, "revenue"),
    ]

    skr04_data = [
        ("8000", "8999", "revenue", "Umsatzerlöse", "Revenue", True, False, "revenue"),
        ("5000", "5199", "material_costs", "Materialaufwand", "Material/COGS", False, True, "cost_of_goods"),
        ("6000", "6199", "personnel_costs", "Personalaufwand", "Personnel Costs", False, True, "personnel"),
        ("6200", "6599", "other_operating_expenses", "Sonstige betriebliche Aufwendungen", "Other Operating Expenses", False, True, "other_operating"),
        ("6800", "6899", "depreciation", "Abschreibungen", "Depreciation & Amortization", False, True, "depreciation"),
        ("7300", "7399", "interest_expense", "Zinsaufwand", "Interest Expense", False, True, "interest"),
        ("7600", "7699", "tax_expense", "Steuern", "Tax Expense", False, True, "tax"),
        ("4000", "4999", "other_income", "Sonstige betriebliche Erträge", "Other Operating Income", True, False, "revenue"),
    ]

    rows = []
    for chart, data in [("skr03", skr03_data), ("skr04", skr04_data)]:
        for start, end, cat, de, en, is_rev, is_cost, section in data:
            rows.append({
                "id": uuid4(), "chart_type": chart,
                "account_code_start": start, "account_code_end": end,
                "standardized_category": cat,
                "display_name_de": de, "display_name_en": en,
                "is_revenue": is_rev, "is_cost": is_cost,
                "pnl_section": section,
            })

    op.bulk_insert(account_mappings, rows)

    # --- variance_results ---
    op.create_table(
        "variance_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("analysis_type", analysis_type, nullable=False),
        sa.Column("standardized_category", sa.String(100), nullable=True),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("comparison_period", sa.Date(), nullable=True),
        sa.Column("variance_pct", sa.Float(), nullable=True),
        sa.Column("variance_abs", sa.Numeric(15, 2), nullable=True),
        sa.Column("significance", significance, nullable=False, server_default="normal"),
        sa.Column("ai_commentary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- benchmark_data ---
    op.create_table(
        "benchmark_data",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("industry", sa.String(255), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- finance_queries ---
    op.create_table(
        "finance_queries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("variance_id", UUID(as_uuid=True), sa.ForeignKey("variance_results.id"), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("status", query_status, nullable=False, server_default="pending_review"),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("finance_queries")
    op.drop_table("benchmark_data")
    op.drop_table("variance_results")
    op.drop_table("account_mappings")
    op.drop_index("ix_line_items_project_period_category", table_name="financial_line_items")
    op.drop_table("financial_line_items")
    op.drop_table("financial_datasets")

    for enum_name in ["chartofaccounts", "datasetstatus", "analysistype",
                      "variancesignificance", "financequerystatus", "pnlsection"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
