import asyncio
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from core.database import get_db
from modules.auth.dependencies import current_user, require_advisor
from modules.auth.models import User
from modules.projects.dependencies import check_project_access
from .models import Document, DocumentText, DocumentTag, Workstream, DocumentStatus, TagSource
from .schemas import (
    DocumentResponse, DocumentTextResponse, StatusUpdateRequest,
    DocumentTagResponse, AddTagRequest, SearchResultResponse,
)
from .storage import save_file, delete_file, read_file
from modules.ocr.extractor import extract_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/plain",
    "text/csv",
}

IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Rule-based document categories for auto-tagging
TAG_RULES: list[tuple[str, list[str]]] = [
    ("contract", ["contract", "agreement", "vertrag", "vereinbarung"]),
    ("financial_statement", ["balance sheet", "income statement", "profit and loss", "p&l", "bilanz", "gewinn"]),
    ("tax_return", ["tax return", "steuererklärung", "tax assessment", "steuerbescheid"]),
    ("audit_report", ["audit report", "prüfungsbericht", "auditor", "wirtschaftsprüfer"]),
    ("corporate_register", ["handelsregister", "commercial register", "articles of association", "satzung", "gesellschaftsvertrag"]),
    ("employment", ["employment contract", "arbeitsvertrag", "works agreement", "betriebsvereinbarung"]),
    ("insurance", ["insurance policy", "versicherung", "coverage", "deckung"]),
    ("ip_patent", ["patent", "trademark", "marke", "license", "lizenz", "intellectual property"]),
    ("real_estate", ["lease agreement", "mietvertrag", "grundbuch", "land register"]),
    ("litigation", ["lawsuit", "klage", "litigation", "rechtsstreit", "court", "gericht"]),
]


def _auto_tag_document(text_content: str) -> list[tuple[str, float]]:
    """Rule-based auto-tagging. Returns list of (tag, confidence) tuples."""
    text_lower = text_content.lower()
    tags = []
    for tag, keywords in TAG_RULES:
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            confidence = min(0.5 + (matches * 0.15), 1.0)
            tags.append((tag, round(confidence, 2)))
    return tags


async def _mark_image_stored(document_id: UUID):
    """Background task: mark image as uploaded (no text extraction available yet)."""
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, document_id)
        if doc:
            doc.status = DocumentStatus.uploaded
            await db.commit()


async def _process_document(document_id: UUID, file_bytes: bytes, mime_type: str, filename: str):
    """Background task: extract text, update search vector, auto-tag."""
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, document_id)
        if not doc:
            return
        try:
            doc.status = DocumentStatus.processing
            await db.commit()

            text_content, page_count = extract_text(file_bytes, mime_type, filename)

            if text_content:
                doc_text = DocumentText(document_id=document_id, content=text_content)
                db.add(doc_text)
                await db.flush()

                # Update full-text search vector
                await db.execute(
                    text(
                        "UPDATE document_texts SET search_vector = to_tsvector('english', content) "
                        "WHERE document_id = :doc_id"
                    ).bindparams(doc_id=document_id)
                )

                # Auto-tag based on content
                tags = _auto_tag_document(text_content)
                for tag_name, confidence in tags:
                    db.add(DocumentTag(
                        document_id=document_id,
                        tag=tag_name,
                        confidence=confidence,
                        source=TagSource.ai,
                    ))

            doc.status = DocumentStatus.under_review
            if page_count:
                doc.page_count = page_count
            await db.commit()
        except Exception as e:
            logger.exception("Document processing failed for %s: %s", document_id, e)
            doc.status = DocumentStatus.failed
            await db.commit()


# --- Upload ---

@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workstream: Workstream = Form(Workstream.general),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    mime = file.content_type or "application/octet-stream"
    is_image = mime in IMAGE_MIME_TYPES
    if mime not in ALLOWED_MIME_TYPES and not is_image:
        raise HTTPException(status_code=415, detail=f"File type not supported: {mime}")

    storage_path = await save_file(file_bytes, file.filename or "upload")

    doc = Document(
        project_id=project_id,
        uploaded_by=user.id,
        name=file.filename or "upload",
        original_filename=file.filename or "upload",
        mime_type=mime,
        size_bytes=len(file_bytes),
        workstream=workstream,
        storage_path=storage_path,
        status=DocumentStatus.uploaded,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    if is_image:
        background_tasks.add_task(_mark_image_stored, doc.id)
    else:
        background_tasks.add_task(_process_document, doc.id, file_bytes, mime, file.filename or "")

    return doc


# --- List & Get ---

@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    project_id: UUID,
    workstream: Workstream | None = Query(None),
    status: DocumentStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    query = select(Document).where(Document.project_id == project_id)
    if workstream:
        query = query.where(Document.workstream == workstream)
    if status:
        query = query.where(Document.status == status)
    query = query.order_by(Document.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{document_id}/text", response_model=DocumentTextResponse)
async def get_document_text(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await db.execute(
        select(DocumentText).where(DocumentText.document_id == document_id)
    )
    doc_text = result.scalar_one_or_none()
    if not doc_text:
        raise HTTPException(status_code=404, detail="Text not yet extracted or document failed processing")
    return doc_text


# --- Search ---

@router.get("/search", response_model=list[SearchResultResponse])
async def search_documents(
    project_id: UUID,
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await db.execute(
        text("""
            SELECT d.id, d.name, d.original_filename, d.workstream, d.status, d.created_at,
                   ts_rank(dt.search_vector, plainto_tsquery('english', :query)) AS rank,
                   ts_headline('english', dt.content, plainto_tsquery('english', :query),
                               'StartSel=**, StopSel=**, MaxWords=40, MinWords=20') AS snippet
            FROM documents d
            JOIN document_texts dt ON dt.document_id = d.id
            WHERE d.project_id = :project_id
              AND dt.search_vector @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT 50
        """).bindparams(query=q, project_id=project_id)
    )
    rows = result.mappings().all()
    return [SearchResultResponse(**row) for row in rows]


# --- Versioning ---

@router.post("/{document_id}/versions", response_model=DocumentResponse, status_code=201)
async def upload_new_version(
    project_id: UUID,
    document_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    parent = await db.get(Document, document_id)
    if not parent or parent.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    mime = file.content_type or parent.mime_type
    storage_path = await save_file(file_bytes, file.filename or parent.original_filename)

    # Find the latest version number in the chain
    root_id = parent.parent_doc_id or parent.id
    max_ver = await db.scalar(
        select(func.max(Document.version_number)).where(
            (Document.id == root_id) | (Document.parent_doc_id == root_id)
        )
    )
    new_version = (max_ver or 1) + 1

    doc = Document(
        project_id=project_id,
        uploaded_by=user.id,
        name=parent.name,
        original_filename=file.filename or parent.original_filename,
        mime_type=mime,
        size_bytes=len(file_bytes),
        workstream=parent.workstream,
        storage_path=storage_path,
        status=DocumentStatus.uploaded,
        version_number=new_version,
        parent_doc_id=root_id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    is_image = mime in IMAGE_MIME_TYPES
    if is_image:
        background_tasks.add_task(_mark_image_stored, doc.id)
    else:
        background_tasks.add_task(_process_document, doc.id, file_bytes, mime, file.filename or "")

    return doc


@router.get("/{document_id}/versions", response_model=list[DocumentResponse])
async def list_versions(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    doc = await db.get(Document, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    root_id = doc.parent_doc_id or doc.id
    result = await db.execute(
        select(Document)
        .where((Document.id == root_id) | (Document.parent_doc_id == root_id))
        .order_by(Document.version_number.desc())
    )
    return result.scalars().all()


# --- Status Workflow ---

VALID_TRANSITIONS = {
    DocumentStatus.uploaded: {DocumentStatus.under_review, DocumentStatus.failed},
    DocumentStatus.under_review: {DocumentStatus.reviewed, DocumentStatus.failed},
    DocumentStatus.reviewed: {DocumentStatus.approved, DocumentStatus.under_review},
    DocumentStatus.approved: {DocumentStatus.reviewed},  # allow reverting
    DocumentStatus.failed: {DocumentStatus.uploaded},     # allow retry
}


@router.patch("/{document_id}/status", response_model=DocumentResponse)
async def update_document_status(
    project_id: UUID,
    document_id: UUID,
    data: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_advisor),
):
    await check_project_access(project_id, user, db)
    doc = await db.get(Document, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    allowed = VALID_TRANSITIONS.get(doc.status, set())
    if data.status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot transition from '{doc.status.value}' to '{data.status.value}'"
        )

    doc.status = data.status
    await db.commit()
    await db.refresh(doc)
    return doc


# --- Tags ---

@router.get("/{document_id}/tags", response_model=list[DocumentTagResponse])
async def list_tags(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    result = await db.execute(
        select(DocumentTag)
        .where(DocumentTag.document_id == document_id)
        .order_by(DocumentTag.confidence.desc().nullslast(), DocumentTag.tag)
    )
    return result.scalars().all()


@router.post("/{document_id}/tags", response_model=DocumentTagResponse, status_code=201)
async def add_tag(
    project_id: UUID,
    document_id: UUID,
    data: AddTagRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    doc = await db.get(Document, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    tag = DocumentTag(
        document_id=document_id,
        tag=data.tag.strip().lower(),
        source=TagSource.manual,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{document_id}/tags/{tag_id}", status_code=204)
async def remove_tag(
    project_id: UUID,
    document_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    tag = await db.get(DocumentTag, tag_id)
    if not tag or tag.document_id != document_id:
        raise HTTPException(status_code=404, detail="Tag not found")
    await db.delete(tag)
    await db.commit()


# --- Delete & Download ---

@router.delete("/{document_id}", status_code=204)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await delete_file(doc.storage_path)
    await db.delete(doc)
    await db.commit()


@router.get("/{document_id}/download")
async def download_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await check_project_access(project_id, user, db)
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        path=doc.storage_path,
        filename=doc.original_filename,
        media_type=doc.mime_type,
    )
