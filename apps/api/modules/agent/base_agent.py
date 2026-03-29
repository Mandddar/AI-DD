"""
Abstract base class for all due diligence agents.
Provides RAG context retrieval (PostgreSQL FTS) and LLM invocation (Groq API).
"""
import json
import logging
from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings
from .embeddings import fts_search

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseAgent(ABC):

    @property
    @abstractmethod
    def agent_type(self) -> str:
        ...

    @abstractmethod
    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        """Return realistic hardcoded findings for dev mode (no Groq key)."""
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
        """Return (text_excerpts, doc_id_strings) of the top relevant chunks via FTS."""
        chunks = await fts_search(query, document_ids, db, top_k=10)
        excerpts = [c.chunk_text[:600] for c in chunks]
        doc_ids = [str(c.document_id) for c in chunks]
        return excerpts, doc_ids

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> list[dict]:
        """Call Groq API (llama-3.3-70b-versatile) and parse JSON findings array."""
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return parsed.get("findings", [])

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

        if not settings.groq_api_key:
            return self._mock_findings(doc_id_strs)

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
