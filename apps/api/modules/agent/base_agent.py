"""
Abstract base class for all due diligence agents.
Provides RAG context retrieval and LLM invocation helpers.
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings
from .embeddings import similarity_search

logger = logging.getLogger(__name__)
settings = get_settings()


def _is_vertex_configured() -> bool:
    return bool(settings.google_cloud_project)


class FindingDict:
    """Type alias for agent finding payloads (plain dicts)."""
    pass


class BaseAgent(ABC):

    @property
    @abstractmethod
    def agent_type(self) -> str:
        ...

    @abstractmethod
    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        """Return realistic hardcoded findings for dev mode (no GCP)."""
        ...

    @abstractmethod
    def _build_prompt(self, context_chunks: list[str]) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) for the LLM."""
        ...

    async def _retrieve_context(
        self,
        query: str,
        document_ids: list[UUID],
        db: AsyncSession,
    ) -> tuple[list[str], list[str]]:
        """Return (text_excerpts, doc_id_strings) of the top relevant chunks."""
        chunks = await similarity_search(query, document_ids, db, top_k=10)
        excerpts = [c.chunk_text[:600] for c in chunks]
        doc_ids = [str(c.document_id) for c in chunks]
        return excerpts, doc_ids

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> list[dict]:
        """Call Gemini-1.5-pro and parse JSON findings array."""
        def _call():
            import vertexai
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            vertexai.init(project=settings.google_cloud_project, location=settings.vertex_ai_location)
            model = GenerativeModel(
                "gemini-1.5-pro",
                system_instruction=system_prompt,
            )
            response = model.generate_content(
                user_prompt,
                generation_config=GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)

        result = await asyncio.to_thread(_call)
        return result.get("findings", [])

    async def analyze(
        self,
        run_id: UUID,
        project_id: UUID,
        document_ids: list[UUID],
        db: AsyncSession,
    ) -> list[dict]:
        """
        Run analysis and return list of finding dicts ready for AgentFinding insertion.
        Each dict: {agent_type, category, title, description, severity, source_doc_ids, source_excerpts}
        """
        doc_id_strs = [str(d) for d in document_ids]

        if not _is_vertex_configured():
            findings = self._mock_findings(doc_id_strs)
        else:
            try:
                primary_query = self._primary_query()
                excerpts, used_doc_ids = await self._retrieve_context(primary_query, document_ids, db)
                system_prompt, user_prompt = self._build_prompt(excerpts)
                raw_findings = await self._call_llm(system_prompt, user_prompt)
                findings = [
                    {
                        "agent_type": self.agent_type,
                        "category": f.get("category", "General"),
                        "title": f.get("title", "Finding"),
                        "description": f.get("description", ""),
                        "severity": f.get("severity", "medium"),
                        "source_doc_ids": used_doc_ids[:3],
                        "source_excerpts": [f.get("source_excerpt", "")] if f.get("source_excerpt") else [],
                    }
                    for f in raw_findings
                ]
            except Exception as e:
                logger.error("Agent %s failed: %s", self.agent_type, e)
                findings = self._mock_findings(doc_id_strs)

        return findings

    def _primary_query(self) -> str:
        """Override to customise the primary RAG retrieval query."""
        return f"{self.agent_type} due diligence key risks and findings"
