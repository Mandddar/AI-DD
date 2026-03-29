"""
Orchestrator: runs as a FastAPI BackgroundTask.
Coordinates all agents, manages run lifecycle, and saves findings.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from core.database import AsyncSessionLocal
from modules.dms.models import Document, DocumentStatus
from .models import AgentRun, AgentFinding, RunStatus
from .embeddings import ensure_document_embedded
from .planning_agent import PlanningAgent
from .legal_agent import LegalAgent
from .tax_agent import TaxAgent
from .finance_agent import FinanceAgent

logger = logging.getLogger(__name__)

_AGENTS = {
    "planning": PlanningAgent(),
    "legal": LegalAgent(),
    "tax": TaxAgent(),
    "finance": FinanceAgent(),
}


async def run_analysis(run_id: UUID) -> None:
    """Background task: execute full agent analysis for a run."""
    async with AsyncSessionLocal() as db:
        run = await db.get(AgentRun, run_id)
        if not run:
            logger.error("AgentRun %s not found", run_id)
            return

        run.status = RunStatus.running
        run.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Load all documents with extracted text (under_review, reviewed, or approved)
            result = await db.execute(
                select(Document)
                .where(Document.project_id == run.project_id)
                .where(Document.status.in_([
                    DocumentStatus.under_review,
                    DocumentStatus.reviewed,
                    DocumentStatus.approved,
                ]))
            )
            documents = list(result.scalars().all())
            document_ids = [doc.id for doc in documents]

            run.total_documents = len(documents)
            await db.commit()

            # Chunk and embed every document (idempotent)
            for doc in documents:
                await ensure_document_embedded(doc.id, db)
                run.processed_documents += 1
                await db.commit()

            # Run each selected agent
            for workstream in run.workstreams:
                agent = _AGENTS.get(workstream)
                if not agent:
                    logger.warning("Unknown workstream: %s", workstream)
                    continue

                findings = await agent.analyze(run_id, run.project_id, document_ids, db)
                for f in findings:
                    db.add(AgentFinding(run_id=run_id, **f))
                await db.commit()

            run.status = RunStatus.completed
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as exc:
            logger.exception("Run %s failed: %s", run_id, exc)
            run.status = RunStatus.failed
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
