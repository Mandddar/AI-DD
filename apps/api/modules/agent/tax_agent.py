from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are a senior M&A tax due diligence agent specialising in sell-side mandates.

STRICT RULES:
- ONLY report findings backed by SPECIFIC numerical evidence from the provided documents (exact amounts, rates, years, jurisdictions).
- Normal tax provision fluctuations are NOT automatically a risk. Tax provisions change with revenue — this is expected and normal.
- Do NOT flag standard tax disclosures as risks. A company reporting its tax provision is normal reporting, not a "potential liability."
- Only flag tax issues where: (a) there is a specific anomaly or inconsistency in the numbers, (b) there is evidence of an ongoing audit/dispute, (c) a specific structure or transaction creates demonstrable exposure, or (d) required documentation is clearly missing.
- If the documents show healthy, normal tax reporting, say so — do not manufacture problems.
- Every finding MUST cite specific numbers or passages from the documents.
- Quality over quantity: return only 3-5 genuinely material tax findings. If fewer issues exist, return fewer findings.

Severity guide:
- critical: Active tax dispute, material underreporting, or structure that creates certain liability
- high: Specific quantified exposure backed by document evidence (e.g., undocumented transfer pricing worth €X)
- medium: Missing tax documentation that should exist (e.g., no TP study for intercompany transactions)
- low: Area to verify with no current evidence of a problem
- info: Observation, no risk

Return a JSON object with a "findings" array. Each finding must have:
  category, title, description, severity (info|low|medium|high|critical), source_excerpt
"""


class TaxAgent(BaseAgent):
    agent_type = "tax"

    def _primary_query(self) -> str:
        return "tax liabilities deferred tax transfer pricing VAT corporate tax R&D credits tax losses"

    def _build_prompt(self, context_chunks: list[str]) -> tuple[str, str]:
        context = "\n\n---\n\n".join(context_chunks)
        user_prompt = f"""Analyse the following financial and tax documents from the data room.

DOCUMENT EXCERPTS:
{context}

IMPORTANT:
- Normal tax provision fluctuations are NOT risks. Only flag genuine anomalies with specific numbers.
- Standard financial reporting (income tax provisions, effective tax rates) is NOT a finding unless there is a clear inconsistency.
- Do NOT classify "tax provision changed from year X to year Y" as a risk — this is normal business.
- Only report issues where you can point to a specific numerical anomaly, missing document, or structural concern.

Return 3-5 genuinely material tax findings. If fewer genuine issues exist, return fewer. Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "tax", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "Transfer Pricing", "severity": "high",
             "title": "Intercompany transactions lack arm's length documentation",
             "description": "No transfer pricing study exists for intercompany licence arrangements. Under OECD guidelines, this creates material audit risk."},
            {**base, "category": "Tax Audits", "severity": "medium",
             "title": "Open tax years without audit clearance",
             "description": "Tax years 2021-2023 remain open without clearance letters from the tax authority."},
        ]
