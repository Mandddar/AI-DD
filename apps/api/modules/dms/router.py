import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from modules.auth.dependencies import current_user
from modules.auth.models import User
from .models import Document, DocumentText, Workstream, DocumentStatus
from .schemas import DocumentResponse, DocumentTextResponse
from .storage import save_file, delete_file
from modules.ocr.extractor import extract_text

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
    """Background task: extract text and update document status."""
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, document_id)
        if not doc:
            return
        try:
            doc.status = DocumentStatus.processing
            await db.commit()

            text, page_count = extract_text(file_bytes, mime_type, filename)

            if text:
                doc_text = DocumentText(document_id=document_id, content=text)
                db.add(doc_text)

            doc.status = DocumentStatus.ready
            if page_count:
                doc.page_count = page_count
            await db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Document processing failed for %s: %s", document_id, e)
            doc.status = DocumentStatus.failed
            await db.commit()


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workstream: Workstream = Form(Workstream.general),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
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
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(_process_document, doc.id, file_bytes, mime, file.filename or "")

    return doc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{document_id}/text", response_model=DocumentTextResponse)
async def get_document_text(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(DocumentText).where(DocumentText.document_id == document_id)
    )
    doc_text = result.scalar_one_or_none()
    if not doc_text:
        raise HTTPException(status_code=404, detail="Text not yet extracted or document failed processing")
    return doc_text


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
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
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        path=doc.storage_path,
        filename=doc.original_filename,
        media_type=doc.mime_type,
    )
