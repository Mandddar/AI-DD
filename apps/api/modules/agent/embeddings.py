"""
RAG pipeline: chunk documents and retrieve relevant pages via PostgreSQL full-text search.
No vectors needed — uses plainto_tsquery + ts_rank for relevance ranking.
"""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from modules.dms.models import DocumentText
from .models import DocumentChunk

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300


def _chunk_text(full_text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(full_text):
        end = start + CHUNK_SIZE
        chunks.append(full_text[start:end])
        if end >= len(full_text):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


async def ensure_document_indexed(document_id: UUID, db: AsyncSession) -> None:
    """Idempotent: chunk a document and build FTS index if not already done."""
    existing = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).limit(1)
    )
    if existing.scalar_one_or_none():
        return  # already processed

    doc_text_row = await db.execute(
        select(DocumentText).where(DocumentText.document_id == document_id)
    )
    doc_text = doc_text_row.scalar_one_or_none()
    if not doc_text or not doc_text.content:
        return

    chunks = _chunk_text(doc_text.content)
    if not chunks:
        return

    for idx, chunk in enumerate(chunks):
        db.add(DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            chunk_text=chunk,
            search_vector=func.to_tsvector("english", chunk),
        ))
    await db.commit()


async def fts_search(
    query: str,
    document_ids: list[UUID],
    db: AsyncSession,
    top_k: int = 10,
) -> list[DocumentChunk]:
    """Return top_k most relevant chunks using PostgreSQL full-text search.
    Uses plainto_tsquery + ts_rank — no vectors, no external embeddings.
    """
    if not document_ids or not query.strip():
        return []

    ts_query = func.plainto_tsquery("english", query)
    rank = func.ts_rank(DocumentChunk.search_vector, ts_query)

    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id.in_(document_ids))
        .where(DocumentChunk.search_vector.op("@@")(ts_query))
        .order_by(rank.desc())
        .limit(top_k)
    )
    chunks = list(result.scalars().all())

    # Fallback: if FTS returns nothing, return first N chunks in document order
    if not chunks:
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(document_ids))
            .order_by(DocumentChunk.chunk_index)
            .limit(top_k)
        )
        chunks = list(result.scalars().all())

    return chunks
