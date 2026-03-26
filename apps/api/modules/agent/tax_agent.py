from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are a senior M&A tax due diligence agent specialising in sell-side mandates.
Analyse the provided document excerpts and identify tax risks including:
- Deferred tax liabilities and assets
- Transfer pricing compliance and documentation
- VAT and indirect tax issues
- Corporate income tax positions and open years
- R&D tax credits (claimed and unclaimed)
- Tax loss carryforwards and their usability post-acquisition
- Withholding tax obligations

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

Identify 4–6 tax due diligence findings. Quantify exposures where possible.
Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "tax", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "Deferred Tax", "severity": "high",
             "title": "€2.4M deferred tax liability on accelerated depreciation",
             "description": "The company has claimed accelerated capital allowances on equipment and software totalling €8.1M over the past four years, creating a cumulative deferred tax liability of approximately €2.4M at a 30% effective rate. This liability will crystallise post-acquisition and must be reflected in the equity bridge. Buyer's tax counsel should confirm the roll-forward position to completion date."},
            {**base, "category": "Transfer Pricing", "severity": "high",
             "title": "Intercompany transactions lack arm's length documentation",
             "description": "The German subsidiary provides software licences to the Irish parent at a fixed annual fee of €420K. No transfer pricing study or benchmarking analysis exists to support the arm's length nature of this arrangement. Under OECD guidelines, the absence of documentation creates a material audit risk. Recommend commissioning a TP study pre-completion and ring-fencing potential adjustment exposure."},
            {**base, "category": "VAT", "severity": "medium",
             "title": "€183K VAT refund claim outstanding for 14 months",
             "description": "A VAT refund of €183K submitted in January 2023 remains outstanding with the tax authority. The company has not followed up formally and there is no correspondence on file. Buyer should obtain a tax authority clearance letter or escrow the refund amount pending resolution, as the claim could be subject to audit and partial disallowance."},
            {**base, "category": "R&D Tax Credits", "severity": "low",
             "title": "Potentially unclaimed R&D tax credits for FY2022–FY2023",
             "description": "Based on the headcount and product development activity visible in payroll records, the company may have qualifying R&D expenditure of c.€1.1M per annum that has not been claimed under the applicable R&D tax credit regime. Management confirmed no claims have been filed. An R&D credit review could generate a cash benefit of €165–220K, representing an upside to the equity consideration."},
        ]
