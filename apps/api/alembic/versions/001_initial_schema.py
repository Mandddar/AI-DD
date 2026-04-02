"""Initial schema — all 11 modules with v1.0 features.

Includes: 2FA, token blacklist, password reset, document versioning,
7-state lifecycle, document tags, full knowledge module.

Revision ID: 001_initial
Revises: None
Create Date: 2026-04-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ─────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── Users ──────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "lead_advisor", "team_advisor", "seller", "buyer", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("disclaimer_accepted", sa.Boolean, default=False, nullable=False),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("totp_enabled", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Token Blacklist ────────────────────────────────────
    op.create_table(
        "token_blacklist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jti", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Password Reset Tokens ──────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("token", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Projects ───────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("legal_form", sa.Enum("GmbH", "AG", "KG", "Other", name="legalform"), nullable=False),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("employee_count", sa.String(50), nullable=True),
        sa.Column("revenue_size", sa.String(100), nullable=True),
        sa.Column("registered_office", sa.String(255), nullable=True),
        sa.Column("deal_type", sa.Enum("share_deal", "asset_deal", name="dealtype"), nullable=False),
        sa.Column("status", sa.Enum("active", "on_hold", "completed", "archived", name="projectstatus"), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "project_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Documents (with versioning + 7-state lifecycle) ────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("workstream", sa.Enum("legal", "tax", "finance", "general", name="workstream"), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("status", sa.Enum(
            "requested", "uploaded", "processing", "ready",
            "under_review", "reviewed", "approved", "rejected", "archived", "failed",
            name="documentstatus"), nullable=False),
        sa.Column("page_count", sa.String(20), nullable=True),
        sa.Column("version_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("parent_doc_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "document_texts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), unique=True, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "document_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="ai"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Agent Runs & Findings ──────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.Enum("pending", "running", "completed", "failed", name="runstatus"), nullable=False),
        sa.Column("workstreams", postgresql.JSON, nullable=False),
        sa.Column("total_documents", sa.Integer, default=0),
        sa.Column("processed_documents", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "agent_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id"), nullable=False, index=True),
        sa.Column("agent_type", sa.Enum("planning", "legal", "tax", "finance", name="agenttype"), nullable=False),
        sa.Column("category", sa.String(200), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.Enum("info", "low", "medium", "high", "critical", name="severity"), nullable=False),
        sa.Column("source_doc_ids", postgresql.JSON, nullable=False),
        sa.Column("source_excerpts", postgresql.JSON, nullable=False),
        sa.Column("status", sa.Enum("pending_review", "approved", "rejected", name="findingstatus"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR, nullable=True),
    )
    op.create_index("ix_document_chunks_search", "document_chunks", ["search_vector"], postgresql_using="gin")

    # FTS trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_chunk_search_vector()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', NEW.chunk_text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_chunk_search_vector ON document_chunks;
        CREATE TRIGGER trg_chunk_search_vector
        BEFORE INSERT OR UPDATE ON document_chunks
        FOR EACH ROW EXECUTE FUNCTION update_chunk_search_vector();
    """)

    # ── Planning ───────────────────────────────────────────
    op.create_table(
        "audit_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), unique=True, nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("current_phase", sa.Enum("basic_data", "risk_analysis", "dialog", "plan_approval", "request_list", name="planningphase"), nullable=False),
        sa.Column("basic_data", postgresql.JSON, nullable=True),
        sa.Column("risk_analysis", postgresql.JSON, nullable=True),
        sa.Column("dialog_history", postgresql.JSON, nullable=True),
        sa.Column("audit_plan_content", postgresql.JSON, nullable=True),
        sa.Column("is_approved", sa.Boolean, default=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "request_list_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("audit_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_plans.id"), nullable=False, index=True),
        sa.Column("item_number", sa.Integer, nullable=False),
        sa.Column("workstream", sa.String(50), nullable=False),
        sa.Column("audit_field", sa.String(255), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer_document", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("open", "partial", "query", "completed", name="requestitemstatus"), nullable=False),
        sa.Column("priority", sa.Enum("high", "medium", "low", name="requestitempriority"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Finance ────────────────────────────────────────────
    op.create_table(
        "financial_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("chart_of_accounts", sa.Enum("SKR03", "SKR04", "custom", name="chartofaccounts"), nullable=True),
        sa.Column("period_from", sa.Date, nullable=True),
        sa.Column("period_to", sa.Date, nullable=True),
        sa.Column("raw_data", postgresql.JSON, nullable=True),
        sa.Column("structure_metadata", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "financial_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_datasets.id"), nullable=False, index=True),
        sa.Column("account_number", sa.String(20), nullable=True),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("period", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "variance_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("analysis_type", sa.String(50), nullable=False),
        sa.Column("results", postgresql.JSON, nullable=False),
        sa.Column("generated_queries", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Reports ────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("report_type", sa.Enum("detailed_workstream", "executive_summary", "consolidated", name="reporttype"), nullable=False),
        sa.Column("report_format", sa.Enum("docx", "xlsx", name="reportformat"), nullable=False),
        sa.Column("workstream", sa.String(50), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", postgresql.JSON, nullable=False),
        sa.Column("edited_content", postgresql.JSON, nullable=True),
        sa.Column("storage_path", sa.String(512), nullable=True),
        sa.Column("is_finalized", sa.Boolean, default=False),
        sa.Column("finalized_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Knowledge ──────────────────────────────────────────
    op.create_table(
        "project_knowledge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("workstream", sa.String(50), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("extra_data", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cross_project_knowledge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("industry", sa.String(100), nullable=False),
        sa.Column("legal_form", sa.String(50), nullable=True),
        sa.Column("company_size", sa.String(50), nullable=True),
        sa.Column("pattern_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("metrics", postgresql.JSONB, nullable=False),
        sa.Column("is_anonymized", sa.Boolean, default=True, nullable=False),
        sa.Column("source_project_count", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Audit Logs (tamper-proof) ──────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("action", sa.Enum(
            "login", "logout", "login_failed", "password_changed",
            "document_uploaded", "document_viewed", "document_downloaded", "document_deleted",
            "project_created", "project_updated", "project_member_added", "project_member_removed",
            "permission_changed", "user_invited", "access_revoked",
            "agent_run_started", "agent_run_completed", "finding_approved", "finding_rejected",
            "report_generated", "report_exported",
            "data_accessed", "data_exported",
            "gdpr_deletion_requested", "gdpr_deletion_completed",
            name="auditaction"), nullable=False, index=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("extra_data", postgresql.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Self-Improvement ───────────────────────────────────
    op.create_table(
        "usage_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pattern_type", sa.String(100), nullable=False),
        sa.Column("module", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("frequency", sa.String(50), nullable=True),
        sa.Column("details", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "improvement_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category", sa.Enum("performance", "accuracy", "user_experience", "prompt_optimization", "workflow", name="suggestioncategory"), nullable=False),
        sa.Column("module", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("expected_benefit", sa.Text, nullable=False),
        sa.Column("suggested_change", sa.Text, nullable=False),
        sa.Column("status", sa.Enum("proposed", "approved", "rejected", "implemented", name="suggestionstatus"), nullable=False),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("improvement_suggestions")
    op.drop_table("usage_patterns")
    op.drop_table("audit_logs")
    op.drop_table("cross_project_knowledge")
    op.drop_table("project_knowledge")
    op.drop_table("reports")
    op.drop_table("variance_analyses")
    op.drop_table("financial_line_items")
    op.drop_table("financial_datasets")
    op.drop_table("request_list_items")
    op.drop_table("audit_plans")
    op.drop_table("document_chunks")
    op.drop_table("agent_findings")
    op.drop_table("agent_runs")
    op.drop_table("document_tags")
    op.drop_table("document_texts")
    op.drop_table("documents")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.drop_table("password_reset_tokens")
    op.drop_table("token_blacklist")
    op.drop_table("users")

    # Drop enums
    for name in [
        "userrole", "legalform", "dealtype", "projectstatus", "workstream",
        "documentstatus", "runstatus", "agenttype", "severity", "findingstatus",
        "planningphase", "requestitemstatus", "requestitempriority", "chartofaccounts",
        "reporttype", "reportformat", "auditaction", "suggestioncategory", "suggestionstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
