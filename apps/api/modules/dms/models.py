import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, BigInteger, Text, Integer, Float, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from core.database import Base


class Workstream(str, enum.Enum):
    legal = "legal"
    tax = "tax"
    finance = "finance"
    general = "general"


class DocumentStatus(str, enum.Enum):
    """Document lifecycle per spec §6.1:
    Requested → Uploaded → Under Review → Reviewed → Approved
    Plus processing states for OCR pipeline: processing, failed
    """
    requested = "requested"
    uploaded = "uploaded"
    processing = "processing"
    under_review = "under_review"
    reviewed = "reviewed"
    approved = "approved"
    failed = "failed"


class TagSource(str, enum.Enum):
    ai = "ai"
    manual = "manual"


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

    # Versioning
    version_number = Column(Integer, nullable=False, default=1)
    parent_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class DocumentText(Base):
    """Extracted text content — one row per document."""
    __tablename__ = "document_texts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    search_vector = Column(TSVECTOR, nullable=True)
    extracted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_document_texts_search_vector", "search_vector", postgresql_using="gin"),
    )


class DocumentTag(Base):
    """Tags for document categorization — AI-generated or manual."""
    __tablename__ = "document_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    tag = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=True)  # 0.0-1.0 for AI tags, null for manual
    source = Column(SAEnum(TagSource), nullable=False, default=TagSource.manual)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
