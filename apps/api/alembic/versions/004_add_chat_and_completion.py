"""Add planning_messages table and project_members completion columns.

Revision ID: 004_chat_completion
Revises: 003_financial_insights
Create Date: 2026-04-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_chat_completion"
down_revision: Union[str, None] = "003_financial_insights"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Planning chat messages
    op.create_table(
        "planning_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("request_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("request_list_items.id"), nullable=True, index=True),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sender_name", sa.String(255), nullable=False),
        sa.Column("sender_role", sa.String(50), nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Deal completion voting columns on project_members
    op.add_column("project_members", sa.Column("completion_approved", sa.String(10), nullable=True))
    op.add_column("project_members", sa.Column("completion_voted_at", sa.DateTime(timezone=True), nullable=True))

    # Source doc names and pages on agent_findings
    op.add_column("agent_findings", sa.Column("source_doc_names", postgresql.JSON, nullable=True, server_default="[]"))
    op.add_column("agent_findings", sa.Column("source_pages", postgresql.JSON, nullable=True, server_default="[]"))


def downgrade() -> None:
    op.drop_column("agent_findings", "source_pages")
    op.drop_column("agent_findings", "source_doc_names")
    op.drop_column("project_members", "completion_voted_at")
    op.drop_column("project_members", "completion_approved")
    op.drop_table("planning_messages")
