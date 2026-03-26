from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are an expert M&A due diligence planning agent for a sell-side mandate.
Your role is to review the provided document excerpts and identify:
- Gaps in the data room (missing documents)
- Recommended audit focus areas and scope
- Key risk areas requiring deeper investigation
- Completeness of the seller's disclosure

Return a JSON object with a "findings" array. Each finding must have:
  category, title, description, severity (info|low|medium|high|critical), source_excerpt
"""


class PlanningAgent(BaseAgent):
    agent_type = "planning"

    def _primary_query(self) -> str:
        return "due diligence document checklist scope completeness audit planning"

    def _build_prompt(self, context_chunks: list[str]) -> tuple[str, str]:
        context = "\n\n---\n\n".join(context_chunks)
        user_prompt = f"""Analyse the following document excerpts from the data room and produce due diligence planning findings.

DOCUMENT EXCERPTS:
{context}

Identify 4–6 planning findings covering: document gaps, scope priorities, risk focus areas, and disclosure completeness.
Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "planning", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "Document Completeness", "severity": "high",
             "title": "Audited financial statements missing for FY2022",
             "description": "The data room contains management accounts for FY2022 but no audited financial statements. Audited figures are required to verify EBITDA and net asset positions before signing. Request statutory accounts immediately."},
            {**base, "category": "Scope Definition", "severity": "medium",
             "title": "23 items outstanding on the document request list",
             "description": "Of the 47 items on the initial document request list, 23 remain unfulfilled. Key gaps include: employment contracts for senior management, all customer contracts above €500K, and the IP assignment register."},
            {**base, "category": "Risk Focus", "severity": "high",
             "title": "Revenue concentration requires deep-dive",
             "description": "Preliminary review indicates significant customer concentration. The planning phase should prioritise analysis of the top 10 customer contracts, renewal terms, and churn history before proceeding to financial modelling."},
            {**base, "category": "Disclosure Quality", "severity": "info",
             "title": "Audit scope confirmed across three workstreams",
             "description": "Legal, Tax, and Financial workstreams are confirmed in scope. Recommended sequencing: Legal first (change of control triggers), then Tax (structure optimisation pre-deal), then Financial (EBITDA bridge and working capital normalisation)."},
        ]
