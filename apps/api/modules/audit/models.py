"""
Audit Module — GDPR-compliant, tamper-proof audit trail.

Tech: SQLAlchemy + PostgreSQL (insert-only table — no UPDATE/DELETE allowed)
Libraries: SQLAlchemy events (auto-log DB ops), FastAPI middleware (log API requests), openpyxl (export)

Design: Insert-only table. Logs are NEVER updated or deleted, not even by admin.
"""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from core.database import Base


class AuditAction(str, enum.Enum):
    # Auth events
    login = "login"
    logout = "logout"
    login_failed = "login_failed"
    password_changed = "password_changed"

    # Document events
    document_uploaded = "document_uploaded"
    document_viewed = "document_viewed"
    document_downloaded = "document_downloaded"
    document_deleted = "document_deleted"

    # Project events
    project_created = "project_created"
    project_updated = "project_updated"
    project_member_added = "project_member_added"
    project_member_removed = "project_member_removed"

    # Permission events
    permission_changed = "permission_changed"
    user_invited = "user_invited"
    access_revoked = "access_revoked"

    # AI events
    agent_run_started = "agent_run_started"
    agent_run_completed = "agent_run_completed"
    finding_approved = "finding_approved"
    finding_rejected = "finding_rejected"

    # Report events
    report_generated = "report_generated"
    report_exported = "report_exported"

    # Data access
    data_accessed = "data_accessed"
    data_exported = "data_exported"

    # GDPR
    gdpr_deletion_requested = "gdpr_deletion_requested"
    gdpr_deletion_completed = "gdpr_deletion_completed"


class AuditLog(Base):
    """
    Tamper-proof audit trail — INSERT ONLY.
    No UPDATE or DELETE operations should ever be performed on this table.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)

    # What
    action = Column(SAEnum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)  # document, project, user, report, etc.
    resource_id = Column(String(100), nullable=True)     # UUID of the resource

    # Details
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Additional context

    # Where
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # When (immutable)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
