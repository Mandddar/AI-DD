"""
Planning service — generates AI content for each phase transition.
Uses Groq API if available, otherwise returns mock data.
"""
import json
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def _call_groq(system_prompt: str, user_prompt: str) -> dict:
    """Call Groq API and return parsed JSON response."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)
    response = await client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


async def generate_risk_analysis(basic_data: dict) -> list[dict]:
    """Phase 2: Generate AI risk analysis based on company profile."""
    if not settings.groq_api_key:
        return _mock_risk_analysis(basic_data)

    try:
        system_prompt = (
            "You are an M&A due diligence planning expert. Analyse the target company profile "
            "and identify key risk areas for due diligence. Return JSON: "
            '{"risks": [{"risk_area": str, "description": str, "severity": "high"|"medium"|"low", "workstream": "legal"|"tax"|"finance"}]}'
        )
        user_prompt = f"Target company profile:\n{json.dumps(basic_data, indent=2)}\n\nIdentify 5-8 key risk areas for due diligence."
        result = await _call_groq(system_prompt, user_prompt)
        return result.get("risks", _mock_risk_analysis(basic_data))
    except Exception as e:
        logger.error("Risk analysis generation failed: %s", e)
        return _mock_risk_analysis(basic_data)


async def generate_dialog_questions(basic_data: dict, risk_analysis: list) -> list[dict]:
    """Phase 3: Generate follow-up questions based on risk analysis."""
    if not settings.groq_api_key:
        return _mock_dialog_questions(basic_data)

    try:
        system_prompt = (
            "You are an M&A due diligence expert. Based on the company profile and identified risks, "
            "generate targeted follow-up questions to gather more information. Return JSON: "
            '{"questions": [{"question": str, "context": str, "related_risk": str}]}'
        )
        user_prompt = (
            f"Company profile:\n{json.dumps(basic_data, indent=2)}\n\n"
            f"Identified risks:\n{json.dumps(risk_analysis, indent=2)}\n\n"
            "Generate 5-7 targeted follow-up questions."
        )
        result = await _call_groq(system_prompt, user_prompt)
        questions = result.get("questions", [])
        return [{"question": q.get("question", ""), "answer": None} for q in questions] or _mock_dialog_questions(basic_data)
    except Exception as e:
        logger.error("Dialog generation failed: %s", e)
        return _mock_dialog_questions(basic_data)


async def generate_audit_plan(basic_data: dict, risk_analysis: list, dialog_history: list) -> dict:
    """Phase 4: Generate the audit plan content for approval."""
    if not settings.groq_api_key:
        return _mock_audit_plan(basic_data)

    try:
        system_prompt = (
            "You are an M&A due diligence expert. Generate a structured audit plan based on the "
            "company profile, risk analysis, and dialog responses. Return JSON with sections: "
            '{"scope": str, "objectives": [str], "workstreams": [{"name": str, "focus_areas": [str], "priority": str}], '
            '"timeline_weeks": int, "key_risks": [str], "resource_requirements": str}'
        )
        user_prompt = (
            f"Company profile:\n{json.dumps(basic_data, indent=2)}\n\n"
            f"Risk analysis:\n{json.dumps(risk_analysis, indent=2)}\n\n"
            f"Dialog responses:\n{json.dumps(dialog_history, indent=2)}\n\n"
            "Generate a comprehensive audit plan."
        )
        result = await _call_groq(system_prompt, user_prompt)
        return result if result.get("scope") else _mock_audit_plan(basic_data)
    except Exception as e:
        logger.error("Audit plan generation failed: %s", e)
        return _mock_audit_plan(basic_data)


def generate_request_list_items(basic_data: dict, risk_analysis: list) -> list[dict]:
    """Phase 5: Generate request list items based on audit plan."""
    company = basic_data.get("company_name", "Target Company")
    items = [
        {"workstream": "Legal", "audit_field": "Corporate Structure", "question": f"Provide the current corporate structure chart for {company} and all subsidiaries.", "priority": "high"},
        {"workstream": "Legal", "audit_field": "Material Contracts", "question": "List all material contracts (>€100k annual value) with key terms, expiry dates, and change-of-control provisions.", "priority": "high"},
        {"workstream": "Legal", "audit_field": "Litigation", "question": "Provide details of all pending, threatened, or settled litigation in the past 3 years.", "priority": "high"},
        {"workstream": "Legal", "audit_field": "IP & Licences", "question": "List all intellectual property (patents, trademarks, licences) owned or licensed by the company.", "priority": "medium"},
        {"workstream": "Legal", "audit_field": "Employment", "question": "Provide employment contracts for all C-suite and senior management, including non-compete and severance provisions.", "priority": "medium"},
        {"workstream": "Tax", "audit_field": "Tax Returns", "question": "Provide corporate tax returns for the last 3 fiscal years with all schedules and attachments.", "priority": "high"},
        {"workstream": "Tax", "audit_field": "Tax Audits", "question": "List all completed, ongoing, or anticipated tax audits with current status and any provisions.", "priority": "high"},
        {"workstream": "Tax", "audit_field": "Transfer Pricing", "question": "Provide transfer pricing documentation and inter-company agreements for all related-party transactions.", "priority": "medium"},
        {"workstream": "Tax", "audit_field": "VAT/GST", "question": "Provide VAT returns and any pending VAT claims or disputes for the last 3 years.", "priority": "medium"},
        {"workstream": "Finance", "audit_field": "Audited Accounts", "question": "Provide audited financial statements (P&L, balance sheet, cash flow) for the last 3 fiscal years.", "priority": "high"},
        {"workstream": "Finance", "audit_field": "Management Accounts", "question": "Provide monthly management accounts (BWA) for the current and prior fiscal year.", "priority": "high"},
        {"workstream": "Finance", "audit_field": "EBITDA Bridge", "question": "Provide a detailed EBITDA bridge showing all normalisation adjustments with supporting evidence.", "priority": "high"},
        {"workstream": "Finance", "audit_field": "Working Capital", "question": "Provide aged debtors, aged creditors, and inventory breakdown as of the latest month-end.", "priority": "medium"},
        {"workstream": "Finance", "audit_field": "Debt & Commitments", "question": "List all debt facilities, guarantees, and off-balance-sheet commitments with terms and maturity dates.", "priority": "medium"},
        {"workstream": "Finance", "audit_field": "Customer Analysis", "question": "Provide revenue breakdown by top 20 customers for the last 3 years, including contract terms.", "priority": "high"},
    ]
    return items


# ── Mock data fallbacks ──────────────────────────────────────

def _mock_risk_analysis(basic_data: dict) -> list[dict]:
    company = basic_data.get("company_name", "Target")
    industry = basic_data.get("industry", "general")
    return [
        {"risk_area": "Financial Statement Quality", "severity": "high", "workstream": "finance",
         "description": f"As a {basic_data.get('legal_form', 'company')} in the {industry} sector, {company}'s financial statements require detailed review of revenue recognition policies and EBITDA normalisation."},
        {"risk_area": "Customer Concentration", "severity": "high", "workstream": "finance",
         "description": "Revenue dependency on key customers must be assessed. Concentration above 30% in any single customer presents material risk."},
        {"risk_area": "Regulatory Compliance", "severity": "medium", "workstream": "legal",
         "description": f"Industry-specific regulatory requirements for the {industry} sector need verification, including licences and permits."},
        {"risk_area": "Tax Structure", "severity": "medium", "workstream": "tax",
         "description": f"The {basic_data.get('deal_type', 'share deal')} structure requires review of tax loss carry-forwards, transfer pricing, and potential tax liabilities."},
        {"risk_area": "Employment & Key Personnel", "severity": "medium", "workstream": "legal",
         "description": f"With {basic_data.get('employee_count', 'N/A')} employees, key person dependencies and employment contract terms require review."},
        {"risk_area": "Material Contracts", "severity": "medium", "workstream": "legal",
         "description": "Change-of-control provisions in material contracts could impact deal value. All significant agreements must be reviewed."},
    ]


def _mock_dialog_questions(basic_data: dict) -> list[dict]:
    company = basic_data.get("company_name", "Target")
    return [
        {"question": f"What percentage of {company}'s revenue comes from the top 5 customers?", "answer": None},
        {"question": "Are there any pending or threatened litigation matters exceeding €50,000?", "answer": None},
        {"question": "Have there been any significant changes in accounting policies in the last 3 years?", "answer": None},
        {"question": "Are there any off-balance-sheet commitments, guarantees, or contingent liabilities?", "answer": None},
        {"question": f"Does {company} have any related-party transactions? If so, describe their nature and value.", "answer": None},
        {"question": "Are there any pending tax audits or disputed tax assessments?", "answer": None},
    ]


def _mock_audit_plan(basic_data: dict) -> dict:
    company = basic_data.get("company_name", "Target")
    return {
        "scope": f"Full-scope sell-side due diligence for {company} covering legal, tax, and financial workstreams.",
        "objectives": [
            "Verify the quality and sustainability of reported earnings (EBITDA)",
            "Identify material legal, tax, and financial risks that could impact valuation",
            "Assess completeness of the data room and flag missing critical documents",
            "Provide independent findings to support the information memorandum",
        ],
        "workstreams": [
            {"name": "Legal", "focus_areas": ["Corporate structure", "Material contracts", "Litigation", "IP", "Employment"], "priority": "high"},
            {"name": "Tax", "focus_areas": ["Corporate tax compliance", "Transfer pricing", "VAT", "Tax provisions"], "priority": "high"},
            {"name": "Finance", "focus_areas": ["EBITDA quality", "Revenue recognition", "Working capital", "Debt", "Customer concentration"], "priority": "high"},
        ],
        "timeline_weeks": 4,
        "key_risks": [
            "Customer concentration above industry benchmark",
            "Potential EBITDA normalisation adjustments",
            "Regulatory compliance in target industry",
        ],
        "resource_requirements": "Lead advisor + 2 team advisors per workstream. External tax specialist recommended.",
    }
