from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are a senior M&A legal due diligence agent specialising in sell-side mandates.

STRICT RULES:
- ONLY report findings backed by SPECIFIC evidence from the provided documents (exact clauses, dates, amounts, party names).
- Do NOT treat general corporate disclosures, positive environmental statements, or standard business practices as legal risks.
- Do NOT speculate about risks that are not evidenced in the documents. If there is no evidence of litigation, do NOT suggest there might be litigation.
- A company stating it complies with regulations or reduces environmental impact is a POSITIVE indicator — never classify this as a risk.
- Normal financial fluctuations (tax provisions changing year-to-year) are NOT litigation exposure unless the documents explicitly mention disputes, audits, or legal proceedings.
- Every finding MUST reference a specific document passage that demonstrates the issue.
- Quality over quantity: return only 3-5 genuinely material legal findings.

Severity guide:
- critical: Active litigation, unresolved regulatory violation, or missing critical legal protection (e.g., no IP assignment for core technology)
- high: Specific contractual risk with evidence (e.g., change-of-control clause in a named contract worth >10% revenue)
- medium: Identified gap in legal documentation that could pose risk if not addressed
- low: Minor documentation gap or area to verify
- info: Observation with no risk implication

Return a JSON object with a "findings" array. Each finding must have:
  category, title, description, severity (info|low|medium|high|critical), source_excerpt
"""


class LegalAgent(BaseAgent):
    agent_type = "legal"

    def _primary_query(self) -> str:
        return "change of control IP ownership compliance litigation employment contracts corporate structure"

    def _build_prompt(self, context_chunks: list[str]) -> tuple[str, str]:
        context = "\n\n---\n\n".join(context_chunks)
        user_prompt = f"""Analyse the following legal documents and contracts from the data room.

DOCUMENT EXCERPTS:
{context}

IMPORTANT:
- Only flag issues where you can cite SPECIFIC evidence from these excerpts.
- Positive statements about compliance, sustainability, or risk reduction are NOT risks.
- Standard financial disclosures (tax provisions, revenue breakdowns) are NOT legal issues unless they explicitly reference disputes or proceedings.
- Do NOT classify normal business operations as risks.

Return 3-5 genuinely material legal findings. Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "legal", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "Change of Control", "severity": "critical",
             "title": "Key customer contracts contain change of control consent clauses",
             "description": "Three of the five largest customer contracts include change of control provisions requiring written consent prior to completion."},
            {**base, "category": "Intellectual Property", "severity": "high",
             "title": "IP assignment gaps for early-stage contractors",
             "description": "Two early-stage developers engaged as contractors have no IP assignment on file. These individuals may retain rights to core product components."},
            {**base, "category": "Employment Law", "severity": "high",
             "title": "Senior engineers lack non-compete obligations",
             "description": "Employment contracts for 4 of 7 senior engineers contain no enforceable non-compete or non-solicitation clauses."},
        ]
