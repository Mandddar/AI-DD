from .base_agent import BaseAgent

SYSTEM_PROMPT = """You are a senior M&A financial due diligence agent specialising in sell-side mandates.

STRICT RULES:
- ONLY report findings backed by SPECIFIC numerical evidence from the provided documents (exact amounts, percentages, periods).
- Normal business metrics and standard financial reporting are NOT findings. Revenue growing, costs increasing proportionally, or margins being stable are NORMAL — not risks.
- Do NOT treat positive company statements (reducing environmental impact, investing in sustainability) as financial risks.
- Only flag financial issues where: (a) there is a specific numerical anomaly or inconsistency, (b) EBITDA normalization adjustments are quantifiable, (c) there is evidence of revenue recognition problems, or (d) working capital or debt levels show specific concerning patterns.
- Fluctuating tax provisions, changing revenue mix, or growing costs are NORMAL unless the rate of change is clearly abnormal and you can quantify why.
- If the company's financials look healthy, say so. Do not manufacture problems.
- Every finding MUST include specific numbers from the documents.
- Quality over quantity: return only 3-5 genuinely material findings. Return fewer if fewer genuine issues exist.

Severity guide:
- critical: Material misstatement, revenue recognition non-compliance, or fraud indicator with evidence
- high: Quantified EBITDA adjustment >5% or concentration risk >40% of revenue
- medium: Working capital anomaly or trend requiring explanation, backed by numbers
- low: Minor item to verify, no current evidence of a material problem
- info: Observation, no risk

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

IMPORTANT:
- Only flag issues where you can cite SPECIFIC numbers that demonstrate an anomaly.
- Normal financial reporting is NOT a finding. Growing revenue, standard margins, and proportional cost increases are expected.
- Do NOT classify positive corporate initiatives (environmental goals, sustainability investments) as financial risks.
- Every finding must include the specific numbers that make it material.

Return 3-5 genuinely material financial findings. Return fewer if the financials look healthy. Return JSON: {{"findings": [...]}}"""
        return SYSTEM_PROMPT, user_prompt

    def _mock_findings(self, document_ids: list[str]) -> list[dict]:
        base = {"agent_type": "finance", "source_doc_ids": document_ids[:1], "source_excerpts": []}
        return [
            {**base, "category": "EBITDA Quality", "severity": "high",
             "title": "One-off items not excluded from reported EBITDA",
             "description": "Reported EBITDA includes non-recurring items that should be normalised. Adjusted EBITDA represents a material reduction."},
            {**base, "category": "Customer Concentration", "severity": "high",
             "title": "Top 3 customers represent >60% of total revenue",
             "description": "Significant customer concentration poses renewal risk. The largest single customer contract expires within 12 months of expected completion."},
        ]
