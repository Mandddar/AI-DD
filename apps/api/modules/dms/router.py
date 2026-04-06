import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from core.database import get_db
from modules.auth.dependencies import current_user, project_manager, project_contributor, project_reader
from modules.auth.models import User
from .models import (
    Document, DocumentText, DocumentTag, Folder, Workstream, DocumentStatus, VALID_STATUS_TRANSITIONS,
)
from .schemas import (
    DocumentResponse, DocumentTextResponse, DocumentTagResponse,
    DocumentTagCreate, DocumentStatusUpdate,
    FolderCreate, FolderResponse, BulkDeleteRequest, BulkStatusUpdateRequest,
)
from .storage import save_file, delete_file
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
    "image/jpeg",
    "image/png",
    "image/tiff",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def _process_document(document_id: UUID, file_bytes: bytes, mime_type: str, filename: str):
    """Background task: extract text, update status, auto-generate AI tags."""
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

                # AI auto-tagging based on extracted text
                await _auto_tag_document(db, document_id, text_content, filename)

            doc.status = DocumentStatus.ready
            if page_count:
                doc.page_count = page_count
            await db.commit()
        except Exception as e:
            logger.error("Document processing failed for %s: %s", document_id, e)
            doc.status = DocumentStatus.failed
            await db.commit()


async def _auto_tag_document(db: AsyncSession, document_id: UUID, text_content: str, filename: str):
    """AI-powered automatic tagging based on document content and filename (spec §6.1)."""
    tags = []

    # Filename-based tagging
    fname_lower = filename.lower()
    filename_tag_map = {
        "contract": "Contract",
        "vertrag": "Contract",
        "invoice": "Invoice",
        "rechnung": "Invoice",
        "balance": "Financial Statement",
        "bilanz": "Financial Statement",
        "tax": "Tax Document",
        "steuer": "Tax Document",
        "audit": "Audit Report",
        "prüfung": "Audit Report",
        "employment": "Employment",
        "arbeits": "Employment",
        "patent": "Intellectual Property",
        "license": "License",
        "lizenz": "License",
        "insurance": "Insurance",
        "versicherung": "Insurance",
        "lease": "Real Estate",
        "miet": "Real Estate",
        "litigation": "Litigation",
        "klage": "Litigation",
        "annual report": "Annual Report",
        "jahresbericht": "Annual Report",
        "shareholder": "Corporate",
        "gesellschafter": "Corporate",
        "articles": "Corporate",
        "satzung": "Corporate",
    }
    for keyword, tag in filename_tag_map.items():
        if keyword in fname_lower:
            tags.append((tag, 0.85))

    # Content-based tagging (keyword analysis on first 5000 chars)
    content_sample = text_content[:5000].lower()
    content_tag_map = {
        "change of control": ("Change of Control", 0.9),
        "kontrollwechsel": ("Change of Control", 0.9),
        "non-disclosure": ("NDA", 0.9),
        "geheimhaltung": ("NDA", 0.9),
        "intellectual property": ("Intellectual Property", 0.85),
        "geistiges eigentum": ("Intellectual Property", 0.85),
        "ebitda": ("Financial Analysis", 0.8),
        "revenue": ("Financial Analysis", 0.7),
        "umsatz": ("Financial Analysis", 0.7),
        "gewinn- und verlust": ("P&L Statement", 0.85),
        "profit and loss": ("P&L Statement", 0.85),
        "cash flow": ("Cash Flow", 0.8),
        "kapitalfluss": ("Cash Flow", 0.8),
        "working capital": ("Working Capital", 0.8),
        "betriebskapital": ("Working Capital", 0.8),
        "pension": ("Pension Obligations", 0.85),
        "betriebsrente": ("Pension Obligations", 0.85),
        "transfer pricing": ("Transfer Pricing", 0.9),
        "verrechnungspreis": ("Transfer Pricing", 0.9),
        "loss carryforward": ("Tax Loss Carryforward", 0.9),
        "verlustvortrag": ("Tax Loss Carryforward", 0.9),
        "due diligence": ("Due Diligence", 0.7),
    }
    for keyword, (tag, conf) in content_tag_map.items():
        if keyword in content_sample:
            tags.append((tag, conf))

    # Deduplicate
    seen = set()
    for tag_name, confidence in tags:
        if tag_name not in seen:
            seen.add(tag_name)
            db.add(DocumentTag(
                document_id=document_id,
                tag=tag_name,
                confidence=confidence,
                source="ai",
            ))


# ── Upload ─────────────────────────────────────────────────

@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workstream: Workstream = Form(Workstream.general),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_contributor),
):
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
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
        version_number=1,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(_process_document, doc.id, file_bytes, mime, file.filename or "")

    return doc


# ── List ───────────────────────────────────────────────────

@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    from modules.auth.models import UserRole

    query = (
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    # Buyers only see approved documents
    if user.role == UserRole.buyer:
        query = query.where(Document.status == DocumentStatus.approved)

    result = await db.execute(query)
    return result.scalars().all()


# ── Get Text ───────────────────────────────────────────────

@router.get("/{document_id}/text", response_model=DocumentTextResponse)
async def get_document_text(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    from modules.auth.models import UserRole

    # Buyers can only access text of approved documents
    if user.role == UserRole.buyer:
        doc = await db.get(Document, document_id)
        if not doc or doc.status != DocumentStatus.approved:
            raise HTTPException(status_code=403, detail="Buyers can only access approved documents")

    result = await db.execute(
        select(DocumentText).where(DocumentText.document_id == document_id)
    )
    doc_text = result.scalar_one_or_none()
    if not doc_text:
        raise HTTPException(status_code=404, detail="Text not yet extracted or document failed processing")
    return doc_text


# ── Flexible auth: Bearer header OR ?token= query param ──
# Needed for <a href> downloads and <iframe> previews where
# the browser cannot send a custom Authorization header.

from fastapi import Request as FastAPIRequest

async def _flexible_project_reader(
    project_id: UUID,
    request: FastAPIRequest,
    token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via Bearer header first; fall back to ?token= query param."""
    from modules.auth.service import get_current_user as svc_get_current_user
    from modules.auth.dependencies import _check_project_membership

    # 1) Try Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            user = await svc_get_current_user(db, auth_header[7:])
            await _check_project_membership(project_id, user, db)
            return user
        except Exception:
            pass

    # 2) Fall back to ?token= query param
    if token:
        try:
            user = await svc_get_current_user(db, token)
            await _check_project_membership(project_id, user, db)
            return user
        except Exception:
            pass

    raise HTTPException(status_code=401, detail="Authentication required. Pass Bearer header or ?token= query param.")


# ── Download ───────────────────────────────────────────────

@router.get("/{document_id}/download")
async def download_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_flexible_project_reader),
):
    """Download a document. Accepts auth via Bearer header OR ?token= query param."""
    from modules.auth.models import UserRole

    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role == UserRole.buyer and doc.status != DocumentStatus.approved:
        raise HTTPException(status_code=403, detail="Buyers can only access approved documents")
    return FileResponse(
        path=doc.storage_path,
        filename=doc.original_filename,
        media_type=doc.mime_type,
    )


@router.get("/{document_id}/preview")
async def preview_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_flexible_project_reader),
):
    """Serve a document inline for in-browser viewing (PDF, images). Auth via Bearer or ?token=."""
    from modules.auth.models import UserRole

    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role == UserRole.buyer and doc.status != DocumentStatus.approved:
        raise HTTPException(status_code=403, detail="Buyers can only access approved documents")

    import os
    if not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    with open(doc.storage_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{doc.original_filename}"',
        },
    )


# ── Delete ─────────────────────────────────────────────────

@router.delete("/{document_id}", status_code=204)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    from sqlalchemy import delete as sql_delete
    from modules.agent.models import DocumentChunk

    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.execute(sql_delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    await db.execute(sql_delete(DocumentText).where(DocumentText.document_id == document_id))
    await db.execute(sql_delete(DocumentTag).where(DocumentTag.document_id == document_id))

    await delete_file(doc.storage_path)
    await db.delete(doc)
    await db.commit()


# ── Status Update (7-state lifecycle) ──────────────────────

@router.patch("/{document_id}/status", response_model=DocumentResponse)
async def update_document_status(
    project_id: UUID,
    document_id: UUID,
    data: DocumentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """
    Update document status through the lifecycle (spec §6.1):
    Requested → Uploaded → Processing → Ready → Under Review → Reviewed → Approved
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not in this project")

    current = doc.status.value
    target = data.status.value
    allowed = VALID_STATUS_TRANSITIONS.get(current, [])

    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{target}'. Allowed: {allowed}",
        )

    doc.status = data.status
    await db.commit()
    await db.refresh(doc)
    return doc


# ── Versioning ─────────────────────────────────────────────

@router.post("/{document_id}/versions", response_model=DocumentResponse, status_code=201)
async def upload_new_version(
    project_id: UUID,
    document_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_contributor),
):
    """Upload a new version of an existing document (spec §6.1 — full document versioning)."""
    parent = await db.get(Document, document_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Document not found")
    if parent.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not in this project")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"File type not supported: {mime}")

    storage_path = await save_file(file_bytes, file.filename or "upload")

    # Find the highest version number in the chain
    root_id = parent.parent_doc_id or parent.id
    result = await db.execute(
        select(func.max(Document.version_number))
        .where(
            (Document.id == root_id) |
            (Document.parent_doc_id == root_id)
        )
    )
    max_version = result.scalar() or 1

    new_doc = Document(
        project_id=project_id,
        uploaded_by=user.id,
        name=parent.name,
        original_filename=file.filename or parent.original_filename,
        mime_type=mime,
        size_bytes=len(file_bytes),
        workstream=parent.workstream,
        storage_path=storage_path,
        status=DocumentStatus.uploaded,
        version_number=max_version + 1,
        parent_doc_id=root_id,
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    background_tasks.add_task(_process_document, new_doc.id, file_bytes, mime, file.filename or "")

    return new_doc


@router.get("/{document_id}/versions", response_model=list[DocumentResponse])
async def list_versions(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """List all versions of a document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    root_id = doc.parent_doc_id or doc.id
    result = await db.execute(
        select(Document)
        .where(
            (Document.id == root_id) |
            (Document.parent_doc_id == root_id)
        )
        .order_by(Document.version_number.desc())
    )
    return result.scalars().all()


# ── Tags ───────────────────────────────────────────────────

@router.get("/{document_id}/tags", response_model=list[DocumentTagResponse])
async def get_document_tags(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """Get all tags for a document (AI-generated and manual)."""
    result = await db.execute(
        select(DocumentTag)
        .where(DocumentTag.document_id == document_id)
        .order_by(DocumentTag.confidence.desc().nullslast())
    )
    return result.scalars().all()


@router.post("/{document_id}/tags", response_model=DocumentTagResponse, status_code=201)
async def add_manual_tag(
    project_id: UUID,
    document_id: UUID,
    data: DocumentTagCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """Add a manual tag to a document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    tag = DocumentTag(
        document_id=document_id,
        tag=data.tag,
        confidence=None,
        source="manual",
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


# ── Full-Text Search ───────────────────────────────────────

@router.get("/search/fulltext")
async def search_documents(
    project_id: UUID,
    q: str = "",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """
    Full-text search across all documents in the project (spec §6.1).
    Uses PostgreSQL tsvector/tsquery via document_chunks for post-OCR search.
    Falls back to ILIKE on document_texts if no chunks exist.
    """
    from modules.auth.models import UserRole

    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

    query_clean = q.strip()

    # Buyers can only search approved documents
    status_filter = "AND d.status = 'approved'" if user.role == UserRole.buyer else ""

    # Try FTS via document_chunks first (GIN-indexed)
    from modules.agent.models import DocumentChunk
    fts_query = text(f"""
        SELECT DISTINCT d.id AS document_id, d.name AS document_name, d.workstream,
               ts_headline('english', dc.chunk_text, plainto_tsquery('english', :q),
                           'MaxWords=40, MinWords=20, StartSel=**, StopSel=**') AS snippet,
               ts_rank(dc.search_vector, plainto_tsquery('english', :q)) AS rank
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE d.project_id = :project_id
          AND dc.search_vector @@ plainto_tsquery('english', :q)
          {status_filter}
        ORDER BY rank DESC
        LIMIT 50
    """)

    result = await db.execute(fts_query, {"q": query_clean, "project_id": str(project_id)})
    rows = result.fetchall()

    if rows:
        return [
            {
                "document_id": str(r.document_id),
                "document_name": r.document_name,
                "workstream": r.workstream,
                "snippet": r.snippet,
                "rank": float(r.rank),
            }
            for r in rows
        ]

    # Fallback: ILIKE search on document_texts
    fallback_query = text(f"""
        SELECT d.id AS document_id, d.name AS document_name, d.workstream,
               SUBSTRING(dt.content FROM 1 FOR 200) AS snippet,
               0.5 AS rank
        FROM document_texts dt
        JOIN documents d ON dt.document_id = d.id
        WHERE d.project_id = :project_id
          AND dt.content ILIKE :pattern
          {status_filter}
        ORDER BY d.created_at DESC
        LIMIT 50
    """)

    result = await db.execute(fallback_query, {"project_id": str(project_id), "pattern": f"%{query_clean}%"})
    rows = result.fetchall()

    return [
        {
            "document_id": str(r.document_id),
            "document_name": r.document_name,
            "workstream": r.workstream,
            "snippet": r.snippet,
            "rank": float(r.rank),
        }
        for r in rows
    ]


# ── Folder Structure ──────────────────────────────────────

@router.post("/folders", response_model=FolderResponse, status_code=201)
async def create_folder(
    project_id: UUID,
    data: FolderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """Create a folder in the project's document structure (spec §6.1)."""
    if data.parent_id:
        parent = await db.get(Folder, data.parent_id)
        if not parent or parent.project_id != project_id:
            raise HTTPException(status_code=404, detail="Parent folder not found")

    folder = Folder(
        project_id=project_id,
        parent_id=data.parent_id,
        name=data.name,
        created_by=user.id,
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


@router.get("/folders", response_model=list[FolderResponse])
async def list_folders(
    project_id: UUID,
    parent_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_reader),
):
    """List folders in a project, optionally filtered by parent."""
    query = select(Folder).where(Folder.project_id == project_id)
    if parent_id:
        query = query.where(Folder.parent_id == parent_id)
    else:
        query = query.where(Folder.parent_id.is_(None))
    query = query.order_by(Folder.name)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(
    project_id: UUID,
    folder_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """Delete a folder (must be empty)."""
    folder = await db.get(Folder, folder_id)
    if not folder or folder.project_id != project_id:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Check for child folders
    children = await db.execute(select(Folder).where(Folder.parent_id == folder_id).limit(1))
    if children.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Folder has subfolders — delete them first")

    # Check for documents in folder
    docs = await db.execute(select(Document).where(Document.folder_id == folder_id).limit(1))
    if docs.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Folder contains documents — move or delete them first")

    await db.delete(folder)
    await db.commit()


@router.post("/init-folders")
async def initialize_folder_structure(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """Auto-generate default folder structure per deal/workstream (spec §6.1)."""
    existing = await db.execute(select(Folder).where(Folder.project_id == project_id).limit(1))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Folder structure already exists")

    default_structure = {
        "Legal": ["Contracts", "Corporate Documents", "Employment", "IP & Licenses", "Litigation", "Insurance"],
        "Tax": ["Tax Returns", "Tax Audits", "Transfer Pricing", "VAT"],
        "Finance": ["Annual Statements", "Interim Reports", "Budget & Planning", "Working Capital"],
        "General": ["Correspondence", "NDA", "Miscellaneous"],
    }

    created = []
    for ws_name, subfolders in default_structure.items():
        ws_folder = Folder(project_id=project_id, name=ws_name, created_by=user.id)
        db.add(ws_folder)
        await db.flush()
        created.append(ws_name)

        for sub_name in subfolders:
            db.add(Folder(project_id=project_id, parent_id=ws_folder.id, name=sub_name, created_by=user.id))

    await db.commit()
    return {"created": created, "total_folders": sum(1 + len(v) for v in default_structure.values())}


# ── Bulk Operations ───────────────────────────────────────

@router.post("/bulk/delete", status_code=200)
async def bulk_delete_documents(
    project_id: UUID,
    data: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """Delete multiple documents at once."""
    from sqlalchemy import delete as sql_delete
    from modules.agent.models import DocumentChunk

    deleted = 0
    for doc_id in data.document_ids:
        doc = await db.get(Document, doc_id)
        if not doc or doc.project_id != project_id:
            continue
        await db.execute(sql_delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
        await db.execute(sql_delete(DocumentText).where(DocumentText.document_id == doc_id))
        await db.execute(sql_delete(DocumentTag).where(DocumentTag.document_id == doc_id))
        await delete_file(doc.storage_path)
        await db.delete(doc)
        deleted += 1

    await db.commit()
    return {"deleted": deleted}


@router.post("/bulk/status", status_code=200)
async def bulk_update_status(
    project_id: UUID,
    data: BulkStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(project_manager),
):
    """Update status of multiple documents at once."""
    updated = 0
    skipped = 0
    target = data.status.value

    for doc_id in data.document_ids:
        doc = await db.get(Document, doc_id)
        if not doc or doc.project_id != project_id:
            skipped += 1
            continue

        current = doc.status.value
        allowed = VALID_STATUS_TRANSITIONS.get(current, [])
        if target in allowed:
            doc.status = data.status
            updated += 1
        else:
            skipped += 1

    await db.commit()
    return {"updated": updated, "skipped": skipped}
