"""Add folders table, document folder_id, and request item assigned_to.

Revision ID: 002_folders_assignments
Revises: 001_initial
Create Date: 2026-04-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_folders_assignments"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Folders table ─────────────────────────────────────
    op.create_table(
        "folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("folders.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Document → folder_id ──────────────────────────────
    op.add_column("documents", sa.Column("folder_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("folders.id"), nullable=True))

    # ── Request list item → assigned_to ───────────────────
    op.add_column("request_list_items", sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("request_list_items", "assigned_to")
    op.drop_column("documents", "folder_id")
    op.drop_table("folders")
