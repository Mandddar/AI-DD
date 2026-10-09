"""Generate the ULTIMATE AI DD Study Guide — combining main + v1.0 branches."""
import sys
sys.path.insert(0, "../apps/api")

from fpdf import FPDF, XPos, YPos


class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "AI DD - Complete Technical Study Guide (Combined)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            self.set_draw_color(201, 168, 76)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def ch(self, t):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(26, 34, 54)
        self.ln(4)
        self.cell(0, 10, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(201, 168, 76)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(6)

    def sec(self, t):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(40, 50, 70)
        self.ln(3)
        self.cell(0, 8, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def sub(self, t):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 70, 90)
        self.ln(2)
        self.cell(0, 6, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def p(self, t):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, t)
        self.ln(2)

    def q(self, t):
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(50, 60, 80)
        y0 = self.get_y()
        self.set_x(15)
        self.multi_cell(180, 5, t)
        self.set_draw_color(201, 168, 76)
        self.set_line_width(0.4)
        self.line(14, y0, 14, self.get_y())
        self.ln(3)

    def code(self, t):
        self.set_font("Courier", "", 7.5)
        self.set_text_color(40, 40, 40)
        self.set_fill_color(240, 241, 243)
        for line in t.split("\n"):
            self.cell(0, 4, "  " + line, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.ln(3)

    def tr(self, cells, hdr=False):
        self.set_font("Helvetica", "B" if hdr else "", 7.5)
        if hdr:
            self.set_fill_color(26, 34, 54)
            self.set_text_color(255, 255, 255)
        else:
            self.set_fill_color(248, 249, 250)
            self.set_text_color(30, 30, 30)
        w = 190 / len(cells)
        for c in cells:
            self.cell(w, 5.5, str(c), border=1, fill=True)
        self.ln()

    def b(self, t, indent=0):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.set_x(15 + indent)
        self.cell(4, 5, "-")
        self.multi_cell(175 - indent, 5, t)
        self.ln(1)

    def gold(self, label, text):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(201, 168, 76)
        self.cell(40, 5, label)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(150, 5, text)
        self.ln(1)

    def qa(self, question, answer):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(26, 34, 54)
        self.multi_cell(0, 5, "Q: " + question)
        self.ln(1)
        self.q(answer)


def build():
    pdf = PDF()
    pdf.alias_nb_pages()

    # ===== COVER =====
    pdf.add_page()
    pdf.ln(35)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(26, 34, 54)
    pdf.cell(0, 15, "AI DD", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(201, 168, 76)
    pdf.cell(0, 10, "AI-Powered M&A Due Diligence Platform", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(40, 50, 70)
    pdf.cell(0, 12, "Complete Technical Study Guide", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Combined: Main Branch + Version 1.0", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.cell(0, 6, "Architecture | Implementation | Algorithms | Interview Preparation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(12)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    for line in [
        "Backend: Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + Celery + Redis",
        "AI/LLM: Groq API (Llama 3.3 70B) | Google Vertex AI (Gemini 1.5 Pro)",
        "Search: PostgreSQL FTS (tsvector) | pgvector (768-dim cosine similarity)",
        "OCR: pymupdf + pytesseract + pypdf + python-docx + openpyxl",
        "Frontend: React 19 + TypeScript + Tailwind CSS + React Query + Zustand",
        "Auth: JWT + bcrypt + 2FA/TOTP + token blacklist + GDPR deletion",
        "Infrastructure: Docker Compose | Google Cloud Run (europe-west3)",
        "",
        "11 Modules | 60+ API Endpoints | 17+ Database Tables | 6 Alembic Migrations",
    ]:
        pdf.cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "April 2026 | CONFIDENTIAL", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # ===== CHAPTER 1: PROJECT OVERVIEW =====
    pdf.add_page()
    pdf.ch("1. Project Overview")

    pdf.sec("The 30-Second Pitch")
    pdf.q("AI DD is an AI-powered M&A Due Diligence platform for advisors and investors. It automates the due diligence process from document collection through AI-assisted analysis to report generation. The core innovation is a RAG-based multi-agent system where four specialized AI agents (Legal, Tax, Finance, Planning) analyze uploaded documents and produce structured findings -- all grounded in actual evidence. Every AI output requires human approval before reaching external parties.")

    pdf.sec("Core Value Proposition")
    pdf.b("Faster due diligence through AI-powered document processing and structured workflows")
    pdf.b("No hallucination by design -- RAG architecture ensures AI only works with uploaded data")
    pdf.b("Active gap identification -- proactively identifies missing information via Smart Question Engine")
    pdf.b("Full human control -- no external communication without explicit approval (HITL principle)")
    pdf.b("GDPR compliant -- EU data residency, audit trail, right to deletion")

    pdf.sec("Two Development Branches")
    pdf.tr(["Feature", "Main Branch", "Version 1.0"], hdr=True)
    pdf.tr(["LLM Provider", "Google Vertex AI (Gemini)", "Groq API (Llama 3.3 70B)"])
    pdf.tr(["RAG Search", "pgvector cosine similarity", "PostgreSQL FTS (tsvector)"])
    pdf.tr(["Task Queue", "BackgroundTasks", "Celery + Redis (configured)"])
    pdf.tr(["Auth", "JWT + 2FA + blacklist + GDPR", "JWT + basic (no 2FA)"])
    pdf.tr(["DMS", "Versioning + tagging + search", "Basic upload + OCR"])
    pdf.tr(["Finance", "SKR detection + German nums", "pandas-based import"])
    pdf.tr(["Reports", "Not built", "Word .docx generation"])
    pdf.tr(["Audit", "Not built", "Middleware logging"])
    pdf.tr(["OCR", "pypdf + python-docx", "pymupdf + pytesseract"])
    pdf.tr(["Migrations", "6 Alembic files", "create_all() only"])
    pdf.tr(["Package Mgr", "pip + requirements.txt", "uv + pyproject.toml"])

    # ===== CHAPTER 2: ARCHITECTURE =====
    pdf.add_page()
    pdf.ch("2. System Architecture")

    pdf.sec("Service Topology")
    pdf.code(
        "React Frontend (:5173)  --->  FastAPI Backend (:8000)\n"
        "                                    |\n"
        "                         +----------+----------+\n"
        "                         |                     |\n"
        "                   PostgreSQL 16          Redis 7\n"
        "                   (:5432/5433)          (:6379/6750)\n"
        "                   + pgvector              Celery\n"
        "                   + tsvector FTS           Worker"
    )

    pdf.sec("Full Tech Stack")
    pdf.tr(["Layer", "Technology", "Purpose"], hdr=True)
    for r in [
        ("Backend", "FastAPI + Python 3.12", "Async REST API"),
        ("ORM", "SQLAlchemy 2.0 (async)", "DB abstraction"),
        ("Database", "PostgreSQL 16 + pgvector", "Data + vectors + FTS"),
        ("AI (v1.0)", "Groq API (Llama 3.3 70B)", "Free-tier LLM"),
        ("AI (main)", "Vertex AI (Gemini 1.5 Pro)", "Enterprise LLM"),
        ("Embeddings", "text-embedding-004 (768d)", "Main branch only"),
        ("FTS", "tsvector + GIN index", "Full-text search"),
        ("OCR", "pymupdf + pytesseract + Pillow", "PDF/image extraction"),
        ("Task Queue", "Celery + Redis", "Background processing"),
        ("Frontend", "React 19 + TypeScript", "SPA"),
        ("Styling", "Tailwind CSS", "Dark M&A-grade UI"),
        ("State", "React Query + Zustand", "Server + client state"),
        ("Auth", "JWT (HS256) + bcrypt", "Tokens + password hashing"),
        ("Reports", "python-docx + openpyxl", "Word/Excel generation"),
    ]:
        pdf.tr(r)

    pdf.sec("11 Backend Modules")
    pdf.tr(["Module", "Endpoints", "Status", "Key Feature"], hdr=True)
    for r in [
        ("Auth", "8-14", "100%", "JWT + roles + 2FA (main) / basic (v1.0)"),
        ("Projects", "5-7", "100%", "CRUD + members + access control"),
        ("DMS", "5-12", "75-90%", "Upload + OCR + versioning (main)"),
        ("Agent", "4", "85%", "4 agents + RAG + Groq/Vertex"),
        ("Planning", "6-9", "100%", "5-phase workflow + AI generation"),
        ("Finance", "5-14", "100%", "Import + variance + SKR (main)"),
        ("Report", "5", "100%*", "Word .docx (v1.0 only)"),
        ("Audit", "2", "100%*", "Middleware logging (v1.0 only)"),
        ("Knowledge", "2", "10%", "Scaffolded, no logic"),
        ("Self-Improve", "3", "10%", "Scaffolded, no logic"),
        ("OCR", "internal", "100%", "pymupdf + pytesseract"),
    ]:
        pdf.tr(r)

    # ===== CHAPTER 3: AUTH DEEP DIVE =====
    pdf.add_page()
    pdf.ch("3. Authentication & Authorization")

    pdf.sec("JWT Token Structure")
    pdf.code(
        "Header:  {alg: HS256, typ: JWT}\n"
        "Payload: {sub: user-uuid, role: admin, type: access,\n"
        "          jti: unique-id (main only), exp: timestamp}\n"
        "Signature: HMAC-SHA256(header.payload, SECRET_KEY)\n"
        "\n"
        "Access token:  60 minutes  (short-lived)\n"
        "Refresh token: 30 days     (for session persistence)"
    )

    pdf.sec("Token Validation Chain")
    pdf.code(
        "Browser: Authorization: Bearer eyJ...\n"
        "  -> HTTPBearer extracts token\n"
        "  -> jwt.decode() verifies signature + expiry\n"
        "  -> Check type == 'access'\n"
        "  -> (Main) Check jti NOT in token_blacklist\n"
        "  -> Load User from DB by payload['sub']\n"
        "  -> Check user.is_active == True\n"
        "  -> Return User object to endpoint"
    )

    pdf.sec("5-Role Permission Matrix")
    pdf.tr(["Role", "Projects", "Docs", "Analysis", "Reports", "Admin"], hdr=True)
    pdf.tr(["Admin", "Full", "Full", "Run+Review", "Generate", "Full"])
    pdf.tr(["Lead Advisor", "Create", "Full", "Run+Review", "Generate", "Audit"])
    pdf.tr(["Team Advisor", "View own", "Upload", "Run+Review", "Drafts", "None"])
    pdf.tr(["Seller", "View own", "Upload", "None", "None", "None"])
    pdf.tr(["Buyer", "Approved", "Approved", "None", "Finalized", "None"])

    pdf.sec("Main Branch Additions (not in v1.0)")
    pdf.b("Token blacklist table -- proper logout (blacklists jti)")
    pdf.b("2FA/TOTP -- pure Python implementation (HMAC-SHA1, RFC 6238)")
    pdf.b("Password reset -- one-time tokens with 1-hour expiry")
    pdf.b("GDPR deletion -- cascades across all tables")
    pdf.b("Settings page -- change password, manage 2FA, delete account")

    pdf.sec("Password Hashing: bcrypt")
    pdf.code(
        "bcrypt.hashpw(password, bcrypt.gensalt())  # ~100ms per hash\n"
        '# Output: "$2b$12$..." ($12$ = 2^12 = 4096 rounds)\n'
        "# Attacker brute force: ~10 passwords/sec (vs 10B/sec with SHA256)"
    )

    # ===== CHAPTER 4: RAG PIPELINE =====
    pdf.add_page()
    pdf.ch("4. RAG Pipeline (Two Implementations)")

    pdf.sec("Main Branch: pgvector + Vertex AI")
    pdf.code(
        "1. CHUNK: Document -> 1500-char chunks (300 overlap)\n"
        "2. EMBED: text-embedding-004 -> 768-dim vector per chunk\n"
        "3. STORE: pgvector column (Vector(768))\n"
        "4. SEARCH: cosine_distance(query_embedding, chunk_embedding)\n"
        "5. GENERATE: Top 10 chunks -> Gemini 1.5 Pro -> JSON findings"
    )

    pdf.sec("Version 1.0: PostgreSQL FTS + Groq")
    pdf.code(
        "1. CHUNK: Document -> 1500-char chunks (300 overlap)\n"
        "2. INDEX: to_tsvector('english', chunk_text) -> GIN index\n"
        "3. SEARCH: plainto_tsquery() + ts_rank() -> top 10 chunks\n"
        "4. GENERATE: Top 10 chunks -> Groq (Llama 3.3 70B) -> JSON\n"
        "\n"
        "Key difference: No vector embeddings needed.\n"
        "PostgreSQL FTS is simpler but less semantic than cosine similarity."
    )

    pdf.sec("Why Two Approaches?")
    pdf.p("pgvector captures semantic similarity ('company acquired' matches 'business purchased'). FTS matches exact terms only. For M&A due diligence where legal language is precise, FTS works surprisingly well. pgvector is better for fuzzy/conceptual queries.")

    pdf.sec("Chunking Algorithm")
    pdf.code(
        "CHUNK_SIZE = 1500 chars  (~1 paragraph)\n"
        "CHUNK_OVERLAP = 300 chars (20%)\n"
        "\n"
        "Chunk 1: [chars 0-1500]\n"
        "Chunk 2: [chars 1200-2700]  <- 300 char overlap\n"
        "Chunk 3: [chars 2400-3900]\n"
        "\n"
        "Overlap ensures passages at boundaries appear in both chunks."
    )

    pdf.sec("4 Specialized Agents")
    pdf.tr(["Agent", "Focus", "Primary Query"], hdr=True)
    pdf.tr(["Planning", "Doc gaps, scope", "due diligence checklist scope completeness"])
    pdf.tr(["Legal", "Contracts, IP, litigation", "change of control IP compliance litigation"])
    pdf.tr(["Tax", "CIT, VAT, transfer pricing", "tax liabilities deferred tax VAT R&D credits"])
    pdf.tr(["Finance", "EBITDA, revenue, WC", "EBITDA revenue recognition working capital"])

    pdf.sec("Anti-Hallucination Rules")
    pdf.b("Layer 1 - RAG: Every answer grounded in uploaded documents with source citations")
    pdf.b("Layer 2 - No-Answer: Returns 'insufficient data' instead of guessing")
    pdf.b("Layer 3 - Strict Prompts: 'Do NOT flag positive statements as risks'")
    pdf.b("Layer 4 - Quality Cap: Maximum 3-5 findings per agent (quality > quantity)")

    # ===== CHAPTER 5: PLANNING MODULE =====
    pdf.add_page()
    pdf.ch("5. Planning Module (The USP)")

    pdf.sec("5-Phase Interactive Workflow")
    phases = [
        ("Phase 1", "Basic Data", "Company name, legal form, industry, employees, revenue, deal type"),
        ("Phase 2", "Risk Analysis", "AI generates 5-12 risk areas based on profile (legal-form, industry, deal-type)"),
        ("Phase 3", "Dialog", "AI asks 5-10 targeted follow-up questions (yes/no, text, multi-choice)"),
        ("Phase 4", "Audit Plan", "Structured plan: workstreams, scope, focus areas, priorities. Human reviews + approves."),
        ("Phase 5", "Request List", "15-40 items across Legal/Tax/Finance with status + priority + Excel export"),
    ]
    for phase, name, desc in phases:
        pdf.gold(f"{phase}: {name}", desc)

    pdf.sec("Risk Analysis Logic (Main Branch)")
    pdf.code(
        "# Rule-based heuristics (no LLM needed):\n"
        "GmbH/AG       -> Corporate Governance risk (high)\n"
        "KG            -> Partnership Structure risk (high)\n"
        "Tech/Software -> IP Ownership (critical), IFRS 15 (high)\n"
        "Manufacturing -> Environmental Liability (high)\n"
        "Share deal    -> Tax Loss Carryforwards s.8c KStG (high)\n"
        "Asset deal    -> Asset Transfer Tax (high)\n"
        "Always        -> Change of Control, Employment, Working Capital"
    )

    pdf.sec("Request List (Standard DD Items)")
    pdf.p("Spec s.11 defines the knowledge base. Main branch generates 40 items (18 Legal, 10 Tax, 12 Finance). V1.0 generates 15 template items.")

    # ===== CHAPTER 6: FINANCE =====
    pdf.add_page()
    pdf.ch("6. Financial Analysis")

    pdf.sec("Main Branch: Intelligent Import Pipeline")
    pdf.code(
        "1. Structure Detection: Scan 20 rows for headers, account codes, periods\n"
        "2. SKR Detection: Revenue in 4xxx=SKR03, 8xxx=SKR04\n"
        "3. German Numbers: '1.234,56' -> remove dots -> comma to dot -> Decimal\n"
        "4. Account Mapping: Lookup ranges in account_mappings table\n"
        "5. UPSERT: ON CONFLICT (project, account, period) DO UPDATE\n"
        "\n"
        "Variance Analysis (all in SQL):\n"
        "  MoM: current month vs prior month per category\n"
        "  YoY: cumulative YTD comparison\n"
        "  Significance: >50%/500K=critical, >25%/100K=significant\n"
        "  Auto-queries: Template-based for significant variances"
    )

    pdf.sec("Version 1.0: Pandas-Based Import")
    pdf.code(
        "1. pandas.read_excel() or read_csv()\n"
        "2. Clean column names, replace NaN\n"
        "3. Store raw_data as JSON\n"
        "4. Variance: mean, std, min, max per column\n"
        "5. Flag significant if variance_pct > 20%"
    )

    pdf.sec("SKR03 vs SKR04 (German Chart of Accounts)")
    pdf.tr(["Range", "SKR03", "SKR04"], hdr=True)
    pdf.tr(["Revenue", "4000-4999", "8000-8999"])
    pdf.tr(["Material/COGS", "5000-5999", "5000-5199"])
    pdf.tr(["Personnel", "6000-6199", "6000-6199"])
    pdf.tr(["Other OpEx", "6200-6599", "6200-6599"])
    pdf.tr(["Depreciation", "6600-6699", "6800-6899"])

    # ===== CHAPTER 7: REPORTS + AUDIT =====
    pdf.add_page()
    pdf.ch("7. Report Generation + Audit Trail")

    pdf.sec("3 Report Types (v1.0)")
    pdf.tr(["Type", "Content", "Format"], hdr=True)
    pdf.tr(["Detailed Workstream", "All findings per workstream, by category", "Word .docx"])
    pdf.tr(["Executive Summary", "Critical + high only, editable before export", "Word .docx"])
    pdf.tr(["Consolidated", "Cross-workstream, grouped by agent type", "Word .docx"])

    pdf.sec("Report Pipeline")
    pdf.code(
        "1. Fetch completed AgentRun rows\n"
        "2. Load AgentFinding rows, deduplicate by title\n"
        "3. Structure content by report type\n"
        "4. Append AI Disclaimer (mandatory)\n"
        "5. On finalize: python-docx creates .docx file\n"
        "6. Locked (is_finalized=True, immutable)"
    )

    pdf.sec("Audit Trail (v1.0)")
    pdf.code(
        "AuditMiddleware on every API request:\n"
        "  - Captures: method, path, status, IP, user-agent\n"
        "  - INSERT-ONLY (never UPDATE/DELETE)\n"
        "  - GDPR tamper-proof design\n"
        "  - Admins see all logs, Lead Advisors see own only\n"
        "  - Skips: /health, /docs, /redoc"
    )

    # ===== CHAPTER 8: FRONTEND =====
    pdf.add_page()
    pdf.ch("8. Frontend Architecture")

    pdf.sec("Route Map")
    pdf.code(
        "PUBLIC: /, /login, /register, /disclaimer\n"
        "PROTECTED:\n"
        "  /dashboard, /projects, /settings\n"
        "  /projects/:id/documents\n"
        "  /projects/:id/planning\n"
        "  /projects/:id/analysis, /analysis/:runId\n"
        "  /projects/:id/finance\n"
        "  /projects/:id/reports\n"
        "  /projects/:id/red-flags\n"
        "  /projects/:id/settings\n"
        "  /admin/users (admin only)\n"
        "  /audit (admin + lead_advisor)"
    )

    pdf.sec("State Management")
    pdf.code(
        "React Query (server state):\n"
        "  - Cache + background refetch + conditional polling\n"
        "  - Documents: poll every 2s while status='processing'\n"
        "  - 30-second staleTime, 1 retry\n"
        "\n"
        "Zustand (client state):\n"
        "  - user: User | null\n"
        "  - isLoading: boolean\n"
        "  - logout(): calls API -> clears localStorage\n"
        "\n"
        "Axios Interceptor:\n"
        "  - Request: adds Bearer token from localStorage\n"
        "  - Response 401: clears tokens -> redirect to /login"
    )

    pdf.sec("Permission Hook (v1.0)")
    pdf.code(
        "const p = usePermissions();\n"
        "p.canCreateProject      // admin, lead_advisor\n"
        "p.canUploadDocuments    // admin, lead, team, seller\n"
        "p.canRunAnalysis        // admin, lead, team\n"
        "p.canManageReports      // admin, lead, team\n"
        "p.onlyFinalizedReports  // buyer only\n"
        "p.isReadOnly            // buyer only"
    )

    # ===== CHAPTER 9: INTERVIEW Q&A =====
    pdf.add_page()
    pdf.ch("9. Interview Questions & Answers")

    pdf.qa("Walk me through the system architecture.",
        "Monorepo with FastAPI backend and React frontend, containerized with Docker Compose (5 services). Backend has 11 modules, each with own models/schemas/router. PostgreSQL for data + vectors + FTS. Two AI approaches: pgvector + Vertex AI (main) or tsvector + Groq (v1.0). Celery + Redis for background tasks. JWT auth with 5-role hierarchy.")

    pdf.qa("Why a monolith instead of microservices?",
        "For v1 targeting SME deals, a monolith gives faster dev velocity, simpler deployment, easier debugging. Each module is architecturally independent (own models, schemas, router) -- a 'modular monolith' that can split later. The spec calls for microservices; we designed module boundaries to support it without premature complexity.")

    pdf.qa("Why PostgreSQL FTS instead of pgvector in v1.0?",
        "Simpler architecture -- no external embedding service needed. For M&A DD where legal language is precise, keyword-based FTS works well. pgvector adds semantic similarity ('company acquired' = 'business purchased') but requires Vertex AI for embeddings. FTS is self-contained in PostgreSQL.")

    pdf.qa("How do you prevent AI hallucination?",
        "4 layers: 1) RAG -- AI only sees uploaded documents. 2) No-answer policy -- returns 'insufficient data' not guesses. 3) Strict prompts -- 'Do NOT flag positive statements as risks.' 4) Quality cap -- max 3-5 findings per agent, quality > quantity.")

    pdf.qa("How does your authentication work?",
        "JWT with access (60min) + refresh (30d) tokens. bcrypt for password hashing. 5-role hierarchy (admin -> buyer). Project-level access via ProjectMember table. Main branch adds: token blacklist for logout, 2FA/TOTP, password reset, GDPR deletion. Every project-scoped endpoint checks membership first.")

    pdf.qa("What happens when Groq API is unavailable?",
        "Silent fallback to hardcoded mock findings. Each agent has realistic mock data (e.g., 'Key customer contracts contain change of control consent clauses' - critical). The architecture is production-ready; the intelligence is conditional on API key. This is a known gap -- users see 'completed' status even with mock data.")

    pdf.qa("How does the financial import handle German accounting?",
        "Main branch: 1) Detect structure by scanning 20 rows for headers/account codes/periods. 2) Detect SKR03 (revenue 4xxx) vs SKR04 (revenue 8xxx). 3) Parse German numbers ('1.234,56' -> 1234.56). 4) Map accounts to standardized categories. 5) UPSERT for monthly appends. V1.0 uses simpler pandas-based parsing.")

    pdf.add_page()
    pdf.qa("What would you do differently if starting over?",
        "1) Set up Alembic from day one -- create_all() doesn't handle schema changes. 2) Add tests early -- zero automated tests is a risk for financial calculations. 3) Wire Celery from the start -- BackgroundTasks are fragile. 4) Use one LLM provider consistently -- having both Vertex AI and Groq splits the codebase.")

    pdf.qa("How would you scale for enterprise?",
        "1) Celery + Redis for persistent task queues. 2) Cloud Storage instead of local disk. 3) Read replicas for PostgreSQL. 4) Parallel agent execution (LangGraph state graphs). 5) Cloud Run on GCP europe-west3 with auto-scaling.")

    pdf.qa("What's the hardest technical problem you solved?",
        "German number parsing for financial imports. German uses comma for decimals and dots for thousands ('1.234.567,89'). English is opposite ('1,234,567.89'). Parsing wrong corrupts every figure. We detect format by scanning sample cells -- if comma + exactly 2 digits at end, it's German. Then transform before Decimal().")

    # ===== CHAPTER 10: NUMBERS =====
    pdf.add_page()
    pdf.ch("10. Numbers to Remember")

    pdf.tr(["Metric", "Value", "Context"], hdr=True)
    nums = [
        ("Modules", "11", "All registered in main.py"),
        ("API Endpoints", "60+", "Across all modules"),
        ("Database Tables", "17+", "All modules combined"),
        ("Docker Services", "5", "PostgreSQL, Redis, API, Celery, Web"),
        ("User Roles", "5", "Admin, Lead, Team, Seller, Buyer"),
        ("Agent Types", "4", "Planning, Legal, Tax, Finance"),
        ("Planning Phases", "5", "Data -> Risk -> Dialog -> Plan -> List"),
        ("Report Types", "3", "Detailed, Executive, Consolidated"),
        ("Chunk Size", "1500 chars", "With 300 char overlap (20%)"),
        ("Embedding Dim", "768 (main)", "text-embedding-004"),
        ("FTS Top-K", "10", "Chunks per agent query"),
        ("LLM (v1.0)", "llama-3.3-70b", "Groq API free tier"),
        ("LLM (main)", "gemini-1.5-pro", "Vertex AI europe-west3"),
        ("LLM Temperature", "0.1-0.2", "Low for consistency"),
        ("JWT Access", "60 minutes", "HS256 algorithm"),
        ("JWT Refresh", "30 days", "Session persistence"),
        ("Max File", "50 MB", "Document upload limit"),
        ("bcrypt Rounds", "2^12 = 4096", "~100ms per hash"),
        ("SKR03 Revenue", "4000-4999", "German chart of accounts"),
        ("SKR04 Revenue", "8000-8999", "Alternative chart"),
        ("DD Request Items", "15-40", "Standard checklist"),
        ("GCP Region", "europe-west3", "Frankfurt (EU only)"),
        ("Est. Cloud Cost", "EUR 100-250/mo", "Cloud Run + SQL + Redis"),
    ]
    for n in nums:
        pdf.tr(n)

    pdf.ln(6)
    pdf.sec("Combined Completion Status")
    pdf.code(
        "Module              Main    v1.0    Best\n"
        "Auth + Security     100%    70%     Main (2FA, blacklist, GDPR)\n"
        "Projects            100%    100%    Equal\n"
        "DMS                  90%    75%     Main (versioning, search, tags)\n"
        "OCR                  40%   100%     v1.0 (pymupdf, pytesseract)\n"
        "AI Agents            45%    85%     v1.0 (Groq, strict prompts)\n"
        "Planning            100%   100%     Main (40 items vs 15)\n"
        "Finance             100%   100%     Main (SKR, German nums)\n"
        "Reports               0%   100%     v1.0 (Word .docx)\n"
        "Audit                 0%   100%     v1.0 (middleware)\n"
        "Knowledge             0%    10%     Both scaffolded\n"
        "Self-Improvement      0%    10%     Both scaffolded\n"
        "Frontend             90%    95%     v1.0 (permissions, pages)\n"
        "Alembic              Yes     No     Main\n"
        "\n"
        "IDEAL: Merge both branches for ~90% spec coverage"
    )

    # Save
    out = "AI_DD_Complete_Study_Guide.pdf"
    pdf.output(out)
    print(f"Generated: {out} ({pdf.page_no()} pages)")


if __name__ == "__main__":
    build()
