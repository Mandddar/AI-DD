from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are a senior M&A financial due diligence agent specialising in sell-side mandates.
Analyse the provided document excerpts and identify financial risks and issues including:
- EBITDA normalisation adjustments (one-off items, owner costs, non-recurring income)
- Revenue recognition policies and compliance with IFRS 15 / local GAAP
- Working capital trends and seasonality
- Customer and revenue concentration risks
- Debt, off-balance-sheet obligations, and net debt definition
- Financial controls and accounting quality

Return a JSON object with a "findings" array. Each finding must have:
  category, title, description, severity (info|low|medium|high|critical), source_excerpt
"""


class FinanceAgent(BaseAgent):
    agent_type = "finance"

    def _primary_query(self) -> str:
        return "EBITDA revenue recognition working capital debt financial controls customer concentration"

    def _build_prompt(self, context_chunks: list[str]) -> tuple[str, str]:
        context = "\n\n---\n\n".join(context_chunks)
        user_prompt = f"""Analyse the following financial statements and management accounts from the data room.

DOCUMENT EXCERPTS:
{context}

Identify 4–6 financial due diligence findings. Quantify impacts where possible.
Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "finance", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "EBITDA Quality", "severity": "high",
             "title": "€340K one-off items not excluded from reported EBITDA",
             "description": "Reported EBITDA of €4.2M includes three items that should be normalised: (1) €180K insurance recovery booked as revenue in Q2, (2) €95K grant income from a non-recurring government scheme, and (3) €65K profit on disposal of surplus equipment. Adjusted EBITDA of €3.86M represents an 8.1% reduction and materially impacts enterprise value at the proposed multiple."},
            {**base, "category": "Revenue Recognition", "severity": "critical",
             "title": "Subscription revenue recognition inconsistent with IFRS 15",
             "description": "The company recognises annual SaaS subscription fees in full on the contract start date rather than rateably over the service period. This is non-compliant with IFRS 15 and results in revenue being overstated in Q1 and understated in Q4. The cumulative deferred revenue adjustment at year-end is estimated at €620K and must be restated. Buyer should require IFRS-compliant restated accounts before proceeding."},
            {**base, "category": "Working Capital", "severity": "medium",
             "title": "Q4 working capital requirement 47% above quarterly average",
             "description": "Working capital analysis reveals significant seasonality: the business requires peak funding of €1.8M in Q4 vs. an average of €1.22M in other quarters, driven by annual contract renewals and prepaid vendor commitments. The normalised working capital peg should be set at the monthly average of €1.35M, not the Q4 peak. Locking at Q4 levels would result in a €450K over-payment by the buyer."},
            {**base, "category": "Customer Concentration", "severity": "high",
             "title": "Top 3 customers represent 67% of total revenue",
             "description": "Three enterprise customers account for 67% of LTM revenue (€8.4M of €12.5M). The largest single customer (28% of revenue) has a contract expiring 8 months post-completion with no renewal clause. Loss of this customer would reduce EBITDA by approximately €1.1M and trigger covenant breaches under any acquisition financing. Recommend earn-out structuring contingent on renewal."},
        ]
