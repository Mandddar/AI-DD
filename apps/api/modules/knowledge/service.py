"""
Knowledge Module — Service layer for populating per-project and cross-project knowledge.

Per-project learning file (spec §10.1):
  - Collects all audit findings and insights
  - Continuously updates risk assessments
  - Dynamically adapts audit plan when new findings emerge

Cross-project learning (spec §10.2):
  - Anonymized — removes company names, personal names, addresses
  - Retains numerical values, risk patterns, legal-form findings, issue frequency
"""
import logging
import re
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .models import ProjectKnowledge, CrossProjectKnowledge
from modules.agent.models import AgentFinding, AgentRun, FindingStatus, RunStatus
from modules.projects.models import Project

logger = logging.getLogger(__name__)


async def populate_project_knowledge(db: AsyncSession, project_id: UUID) -> list[ProjectKnowledge]:
    """
    Populate per-project knowledge from approved agent findings.
    Creates ProjectKnowledge entries for each unique finding.
    """
    # Get all approved findings for this project
    result = await db.execute(
        select(AgentFinding)
        .join(AgentRun, AgentFinding.run_id == AgentRun.id)
        .where(AgentRun.project_id == project_id)
        .where(AgentFinding.status == FindingStatus.approved)
        .order_by(AgentFinding.created_at.desc())
    )
    findings = list(result.scalars().all())

    if not findings:
        return []

    # Get existing knowledge titles to avoid duplicates
    existing = await db.execute(
        select(ProjectKnowledge.title)
        .where(ProjectKnowledge.project_id == project_id)
    )
    existing_titles = set(existing.scalars().all())

    new_entries = []
    for finding in findings:
        if finding.title in existing_titles:
            continue

        # Map agent finding to knowledge category
        category = _finding_to_category(finding)

        entry = ProjectKnowledge(
            project_id=project_id,
            category=category,
            workstream=finding.agent_type.value if finding.agent_type else None,
            title=finding.title,
            content=finding.description,
            extra_data={
                "severity": finding.severity.value if finding.severity else None,
                "source_finding_id": str(finding.id),
                "source_doc_ids": finding.source_doc_ids,
                "source_excerpts": finding.source_excerpts[:3] if finding.source_excerpts else [],
            },
        )
        db.add(entry)
        new_entries.append(entry)
        existing_titles.add(finding.title)

    if new_entries:
        await db.commit()
        for entry in new_entries:
            await db.refresh(entry)

    logger.info("Populated %d new knowledge entries for project %s", len(new_entries), project_id)
    return new_entries


def _finding_to_category(finding: AgentFinding) -> str:
    """Map an agent finding to a knowledge category."""
    severity = finding.severity.value if finding.severity else "medium"
    if severity in ("high", "critical"):
        return "risk_finding"
    elif "risk" in (finding.title or "").lower() or "risk" in (finding.category or "").lower():
        return "risk_update"
    elif severity == "info":
        return "insight"
    else:
        return "pattern"


# ── PII Anonymization for Cross-Project Knowledge ─────────

# Simple regex-based PII detection (does not require presidio at runtime)
PII_PATTERNS = [
    (re.compile(r'\b[A-Z][a-zäöü]+\s+(?:GmbH|AG|KG|e\.K\.|OHG|UG)\b'), "[COMPANY]"),
    (re.compile(r'\b(?:Herrn?|Frau|Mr\.?|Mrs\.?|Ms\.?)\s+\w+\b'), "[NAME]"),
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), "[EMAIL]"),
    (re.compile(r'\b\d{5}\s+[A-ZÄÖÜ][a-zäöü]+\b'), "[ADDRESS]"),  # German ZIP + city
    (re.compile(r'\b(?:\+49|0049|0)\d{3,5}[\s/-]?\d{4,10}\b'), "[PHONE]"),
    (re.compile(r'\bDE\d{9}\b'), "[TAX_ID]"),  # German VAT ID
    (re.compile(r'\b\d{2,3}/\d{3}/\d{5}\b'), "[TAX_NUMBER]"),  # German Steuernummer
]


def anonymize_text(text: str) -> str:
    """Remove PII from text for cross-project knowledge base."""
    result = text
    for pattern, replacement in PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


async def sync_cross_project_knowledge(db: AsyncSession) -> int:
    """
    Aggregate approved findings across all projects into anonymized cross-project knowledge.
    Groups by industry + legal_form + pattern type. Removes all PII.
    """
    # Get all projects with completed agent runs
    result = await db.execute(
        select(Project)
        .where(
            Project.id.in_(
                select(AgentRun.project_id)
                .where(AgentRun.status == RunStatus.completed)
                .distinct()
            )
        )
    )
    projects = list(result.scalars().all())

    if not projects:
        return 0

    new_count = 0

    # Group findings by industry + severity pattern
    for project in projects:
        industry = project.industry or "Unknown"
        legal_form = project.legal_form.value if project.legal_form else None

        # Get approved findings for this project
        findings_result = await db.execute(
            select(AgentFinding)
            .join(AgentRun, AgentFinding.run_id == AgentRun.id)
            .where(AgentRun.project_id == project.id)
            .where(AgentFinding.status == FindingStatus.approved)
        )
        findings = list(findings_result.scalars().all())

        if not findings:
            continue

        # Group by agent_type (workstream) and severity
        from collections import Counter
        severity_counts = Counter(f.severity.value for f in findings if f.severity)
        category_counts = Counter(f.category for f in findings if f.category)

        # Check if we already have a cross-project entry for this industry
        existing = await db.scalar(
            select(CrossProjectKnowledge)
            .where(CrossProjectKnowledge.industry == industry)
            .where(CrossProjectKnowledge.legal_form == legal_form)
            .where(CrossProjectKnowledge.pattern_type == "finding_frequency")
        )

        if existing:
            # Update existing entry — increment source count and merge metrics
            old_metrics = existing.metrics or {}
            old_severity = old_metrics.get("severity_distribution", {})
            for k, v in severity_counts.items():
                old_severity[k] = old_severity.get(k, 0) + v
            old_metrics["severity_distribution"] = old_severity
            old_metrics["total_findings"] = old_metrics.get("total_findings", 0) + len(findings)

            existing.metrics = old_metrics
            existing.source_project_count = str(int(existing.source_project_count or "0") + 1)
            # Flag as updated
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(existing, "metrics")
        else:
            # Create anonymized description from top findings
            top_findings = sorted(findings, key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(f.severity.value, 5))[:5]
            descriptions = [anonymize_text(f.description) for f in top_findings]
            summary = " | ".join(descriptions[:3])

            entry = CrossProjectKnowledge(
                industry=industry,
                legal_form=legal_form,
                company_size=project.employee_count,
                pattern_type="finding_frequency",
                description=anonymize_text(summary),
                metrics={
                    "total_findings": len(findings),
                    "severity_distribution": dict(severity_counts),
                    "top_categories": dict(category_counts.most_common(5)),
                },
                is_anonymized=True,
                source_project_count="1",
            )
            db.add(entry)
            new_count += 1

    await db.commit()
    logger.info("Cross-project sync complete: %d new entries", new_count)
    return new_count
