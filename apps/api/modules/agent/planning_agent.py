from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are an expert M&A due diligence planning agent for a sell-side mandate.

STRICT RULES:
- ONLY report findings that are directly supported by concrete evidence in the provided documents.
- Do NOT flag positive statements, achievements, or goals as risks. A company saying "we reduce our environmental impact" is a POSITIVE indicator, not a compliance risk.
- Do NOT speculate. If the documents don't contain evidence of a problem, do NOT invent one.
- Do NOT treat normal business disclosures (tax provisions, revenue figures) as risks unless there is a clear anomaly or red flag.
- Every finding MUST cite specific evidence (numbers, clauses, dates) from the documents.
- If the data room is incomplete, say what is MISSING — do not fabricate risks from what IS present.
- Quality over quantity: return only 3-5 genuinely material findings. Do not pad the list.

Your role: identify GAPS in the data room (missing documents), recommend audit SCOPE, and flag areas requiring deeper investigation based on ACTUAL evidence of problems.

Return a JSON object with a "findings" array. Each finding must have:
  category, title, description, severity (info|low|medium|high|critical), source_excerpt

Severity guide:
- critical: Deal-breaker or material misstatement found in documents
- high: Significant gap or anomaly backed by specific evidence
- medium: Notable missing documents or incomplete disclosure
- low: Minor gaps or areas to verify
- info: Observations with no risk implication
"""


class PlanningAgent(BaseAgent):
    agent_type = "planning"

    def _primary_query(self) -> str:
        return "due diligence document checklist scope completeness audit planning"

    def _build_prompt(self, context_chunks: list[str]) -> tuple[str, str]:
        context = "\n\n---\n\n".join(context_chunks)
        user_prompt = f"""Analyse the following document excerpts from the data room.

DOCUMENT EXCERPTS:
{context}

Based ONLY on what is present or clearly absent in these excerpts:
1. Identify genuinely missing critical documents (not assumptions)
2. Flag specific anomalies or inconsistencies you can point to with evidence
3. Recommend audit focus areas based on concrete evidence of risk

Do NOT flag positive company statements as risks. Do NOT invent problems where the evidence shows normal operations.

Return 3-5 material findings only. Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "planning", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "Document Completeness", "severity": "high",
             "title": "Audited financial statements missing for FY2022",
             "description": "The data room contains management accounts for FY2022 but no audited financial statements. Audited figures are required to verify EBITDA and net asset positions before signing."},
            {**base, "category": "Scope Definition", "severity": "medium",
             "title": "Employment contracts for senior management not provided",
             "description": "Key employment contracts including non-compete and change-of-control provisions for C-suite executives are absent from the data room."},
            {**base, "category": "Risk Focus", "severity": "high",
             "title": "Revenue concentration requires deep-dive",
             "description": "Preliminary review indicates significant customer concentration. The top customer contracts, renewal terms, and churn history should be prioritised."},
        ]
