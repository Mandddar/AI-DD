import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class Workstream(str, enum.Enum):
    legal = "legal"
    tax = "tax"
    finance = "finance"
    general = "general"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    workstream = Column(SAEnum(Workstream), nullable=False, default=Workstream.general)

    # Storage — local path for now, GCS URI later
    storage_path = Column(String(512), nullable=False)

    status = Column(SAEnum(DocumentStatus), nullable=False, default=DocumentStatus.uploaded)
    page_count = Column(String(20), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class DocumentText(Base):
    """Extracted text content — one row per document."""
    __tablename__ = "document_texts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    extracted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
