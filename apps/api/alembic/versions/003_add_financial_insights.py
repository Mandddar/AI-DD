"""Add financial_insights table for AI-extracted financial analysis.

Revision ID: 003_financial_insights
Revises: 002_folders_assignments
Create Date: 2026-04-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_financial_insights"
down_revision: Union[str, None] = "002_folders_assignments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "financial_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("extracted_figures", postgresql.JSON, nullable=True),
        sa.Column("kpis", postgresql.JSON, nullable=True),
        sa.Column("variance_results", postgresql.JSON, nullable=True),
        sa.Column("anomalies", postgresql.JSON, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("source_document_ids", postgresql.JSON, nullable=True),
        sa.Column("source_dataset_ids", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("financial_insights")
