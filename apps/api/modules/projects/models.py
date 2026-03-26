import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class DealType(str, enum.Enum):
    share_deal = "share_deal"
    asset_deal = "asset_deal"


class ProjectStatus(str, enum.Enum):
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    archived = "archived"


class LegalForm(str, enum.Enum):
    gmbh = "GmbH"
    ag = "AG"
    kg = "KG"
    other = "Other"


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    legal_form = Column(SAEnum(LegalForm), nullable=False, default=LegalForm.gmbh)
    industry = Column(String(255), nullable=True)
    employee_count = Column(String(50), nullable=True)
    revenue_size = Column(String(100), nullable=True)
    registered_office = Column(String(255), nullable=True)
    deal_type = Column(SAEnum(DealType), nullable=False, default=DealType.share_deal)
    status = Column(SAEnum(ProjectStatus), nullable=False, default=ProjectStatus.active)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
