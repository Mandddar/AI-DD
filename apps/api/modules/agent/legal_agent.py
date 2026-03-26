from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are a senior M&A legal due diligence agent specialising in sell-side mandates.
Analyse the provided document excerpts and identify legal risks including:
- Change of control clauses in material contracts
- Intellectual property ownership and assignment gaps
- Regulatory compliance issues
- Litigation exposure and contingent liabilities
- Corporate structure anomalies
- Employee and employment law risks

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

Identify 4–7 legal due diligence findings. Focus on deal-critical issues.
Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "legal", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "Change of Control", "severity": "critical",
             "title": "Key customer contracts contain change of control consent clauses",
             "description": "Three of the five largest customer contracts (representing ~52% of ARR) include change of control provisions requiring written consent from the counterparty prior to completion. Failure to obtain consent could result in contract termination. Buyer must engage with these customers before signing or structure an appropriate condition precedent."},
            {**base, "category": "Intellectual Property", "severity": "high",
             "title": "IP assignment gaps — two founding developers not covered",
             "description": "The company's IP assignment agreement covers 8 of 10 historical software contributors. Two early-stage developers (engaged as contractors in 2019–2020) have no IP assignment on file. These individuals may retain rights to core product components. Legal team to pursue retroactive assignments or assess materiality of their contributions."},
            {**base, "category": "Employment Law", "severity": "high",
             "title": "Senior engineers not subject to non-compete obligations",
             "description": "Employment contracts for 4 of the 7 senior engineers (including the CTO) contain no enforceable non-compete or non-solicitation clauses. Post-completion, key technical staff could join competitors or establish competing ventures. Recommend renegotiating contracts as a condition of completion or discounting valuation to reflect key-man risk."},
            {**base, "category": "Regulatory Compliance", "severity": "medium",
             "title": "GDPR data processing agreements absent for three sub-processors",
             "description": "The company uses three cloud infrastructure sub-processors for which no Data Processing Agreements (DPAs) are in place. Under GDPR Article 28, a controller must have a DPA with all processors. This creates a regulatory exposure and potential supervisory authority notification obligation. DPAs should be executed pre-completion."},
        ]
