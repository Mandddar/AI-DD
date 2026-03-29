"""DMS Phase 2: versioning, full-text search, document tags.

Revision ID: 004_dms_phase2
Revises: 003_2fa_reset
Create Date: 2026-03-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR

revision: str = "004_dms_phase2"
down_revision: Union[str, None] = "003_2fa_reset"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Document versioning columns ---
    op.add_column("documents", sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("documents", sa.Column("parent_doc_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_documents_parent", "documents", "documents", ["parent_doc_id"], ["id"])

    # --- Full-text search on document_texts ---
    op.add_column("document_texts", sa.Column("search_vector", TSVECTOR(), nullable=True))
    op.create_index("ix_document_texts_search_vector", "document_texts", ["search_vector"], postgresql_using="gin")

    # Auto-update search_vector trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION document_texts_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', COALESCE(NEW.content, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER document_texts_search_vector_trigger
        BEFORE INSERT OR UPDATE OF content ON document_texts
        FOR EACH ROW
        EXECUTE FUNCTION document_texts_search_vector_update();
    """)

    # Backfill search_vector for existing rows
    op.execute("UPDATE document_texts SET search_vector = to_tsvector('english', content)")

    # --- Document tags table ---
    op.create_table(
        "document_tags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.Enum("ai", "manual", name="tagsource"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("document_tags")
    op.execute("DROP TYPE IF EXISTS tagsource")

    op.execute("DROP TRIGGER IF EXISTS document_texts_search_vector_trigger ON document_texts")
    op.execute("DROP FUNCTION IF EXISTS document_texts_search_vector_update()")
    op.drop_index("ix_document_texts_search_vector", table_name="document_texts")
    op.drop_column("document_texts", "search_vector")

    op.drop_constraint("fk_documents_parent", "documents", type_="foreignkey")
    op.drop_column("documents", "parent_doc_id")
    op.drop_column("documents", "version_number")
