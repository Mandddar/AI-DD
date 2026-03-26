"""
RAG pipeline: chunk documents, generate embeddings, vector similarity search.
Falls back to keyword-order when Vertex AI is not configured (dev mode).
"""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import get_settings
from modules.dms.models import DocumentText
from .models import DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300
EMBEDDING_DIM = 768


def _chunk_text(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _is_vertex_configured() -> bool:
    return bool(settings.google_cloud_project)


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Vertex AI text-embedding-004, or zero vectors in dev mode."""
    if not _is_vertex_configured():
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    import asyncio

    def _call():
        import vertexai
        from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
        vertexai.init(project=settings.google_cloud_project, location=settings.vertex_ai_location)
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        inputs = [TextEmbeddingInput(t, "RETRIEVAL_DOCUMENT") for t in texts]
        return [e.values for e in model.get_embeddings(inputs)]

    return await asyncio.to_thread(_call)


async def ensure_document_embedded(document_id: UUID, db: AsyncSession) -> None:
    """Idempotent: chunk and embed a document if not already done."""
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

    embeddings = await _embed_texts(chunks)
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        db.add(DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            chunk_text=chunk,
            embedding=emb,
        ))
    await db.commit()


async def similarity_search(
    query: str,
    document_ids: list[UUID],
    db: AsyncSession,
    top_k: int = 10,
) -> list[DocumentChunk]:
    """Return top_k most relevant chunks from the given documents."""
    if not document_ids:
        return []

    if _is_vertex_configured():
        query_emb = (await _embed_texts([query]))[0]
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(document_ids))
            .where(DocumentChunk.embedding.isnot(None))
            .order_by(DocumentChunk.embedding.cosine_distance(query_emb))
            .limit(top_k)
        )
    else:
        # Dev fallback: return first N chunks in document order
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(document_ids))
            .limit(top_k)
        )

    return list(result.scalars().all())
