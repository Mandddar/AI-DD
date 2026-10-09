"""Generate AI DD v1.0 Complete Study Guide PDF."""
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
            self.cell(0, 8, "AI DD v1.0 - Complete Technical Study Guide", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
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
    pdf.ln(40)
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
    pdf.cell(0, 8, "Version 1.0 Branch | Architecture + Implementation + Interview Prep", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    for line in [
        "Backend: Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + Celery + Redis",
        "AI/LLM: Groq API (Llama 3.3 70B) with mock fallback",
        "Search: PostgreSQL Full-Text Search (tsvector + GIN)",
        "OCR: pymupdf + pytesseract + Pillow",
        "Frontend: React 19 + TypeScript + Tailwind CSS + React Query + Zustand",
        "Infrastructure: Docker Compose (5 services) + uv package manager",
        "11 Modules | 5 Docker Services | 60+ API Endpoints | 17+ Database Tables",
    ]:
        pdf.cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "April 2026 | CONFIDENTIAL", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # ===== CH1: ARCHITECTURE =====
    pdf.add_page()
    pdf.ch("1. System Architecture")
    pdf.sec("Tech Stack")
    pdf.tr(["Layer", "Technology", "Purpose"], hdr=True)
    for r in [
        ("Backend", "FastAPI + Python 3.12", "Async REST API framework"),
        ("ORM", "SQLAlchemy 2.0 (async)", "Database abstraction + migrations"),
        ("Database", "PostgreSQL 16", "Primary data store + FTS + pgvector"),
        ("Search", "PostgreSQL tsvector + GIN", "Full-text search (no vector DB)"),
        ("AI/LLM", "Groq API (Llama 3.3 70B)", "Agent analysis + planning generation"),
        ("Task Queue", "Celery + Redis", "Background OCR + agent processing"),
        ("OCR", "pymupdf + pytesseract", "PDF/image text extraction"),
        ("Frontend", "React 19 + TypeScript", "Single-page application"),
        ("Styling", "Tailwind CSS", "Dark luxurious M&A-grade UI"),
        ("State", "React Query + Zustand", "Server state + client state"),
        ("Package Mgr", "uv (Python) + npm (JS)", "Fast dependency management"),
        ("Containers", "Docker Compose", "5 services orchestration"),
    ]:
        pdf.tr(r)

    pdf.ln(4)
    pdf.sec("Service Topology (Docker Compose)")
    pdf.code(
        "PostgreSQL 16  (:5433) -- Primary database\n"
        "Redis 7        (:6750) -- Celery broker + cache\n"
        "FastAPI API    (:8000) -- Backend REST API\n"
        "Celery Worker  (----)  -- Background task processing\n"
        "React/Vite     (:5173) -- Frontend dev server"
    )

    pdf.sec("11 Registered Modules")
    pdf.tr(["Module", "Status", "Endpoints", "Key Technology"], hdr=True)
    for r in [
        ("Auth", "100%", "8", "JWT + bcrypt + role hierarchy"),
        ("Projects", "100%", "5", "CRUD + member management"),
        ("DMS", "100%", "5", "Upload + OCR + FTS chunking"),
        ("OCR", "100%", "internal", "pymupdf + pytesseract + pandas"),
        ("Agent", "85%*", "4", "Groq API + FTS RAG + 4 agents"),
        ("Planning", "100%", "6", "5-phase workflow + Groq AI"),
        ("Finance", "100%", "5", "pandas + numpy variance"),
        ("Report", "100%", "5", "python-docx + .docx export"),
        ("Audit", "100%", "2", "Middleware + insert-only logs"),
        ("Knowledge", "10%", "2", "Models only, no logic"),
        ("Self-Improve", "10%", "3", "Models only, no logic"),
    ]:
        pdf.tr(r)
    pdf.p("* Agent module returns mock findings when GROQ_API_KEY is not configured")

    # ===== CH2: AUTH =====
    pdf.add_page()
    pdf.ch("2. Authentication & Authorization")

    pdf.sec("JWT Token Flow")
    pdf.code(
        "1. POST /auth/login  {email, password}\n"
        "2. Server: bcrypt.verify(password, stored_hash)\n"
        "3. Server: jwt.encode({sub: user_id, role: admin, type: access, exp: +60min})\n"
        "4. Response: {access_token, refresh_token, token_type: bearer}\n"
        "5. Client: localStorage.setItem('access_token', token)\n"
        "6. Every request: Authorization: Bearer <token>\n"
        "7. Server: jwt.decode() -> verify signature + expiry -> load User"
    )

    pdf.sec("5-Role Hierarchy (Spec 4.1)")
    pdf.tr(["Role", "Projects", "Documents", "Analysis", "Reports", "Admin"], hdr=True)
    pdf.tr(["Admin", "Full CRUD", "Full CRUD", "Run+Review", "Generate", "Full"])
    pdf.tr(["Lead Advisor", "Create+Manage", "Full CRUD", "Run+Review", "Generate", "Audit only"])
    pdf.tr(["Team Advisor", "View assigned", "Upload+View", "Run+Review", "View drafts", "None"])
    pdf.tr(["Seller", "View own", "Upload only", "None", "None", "None"])
    pdf.tr(["Buyer", "View approved", "View approved", "None", "Finalized only", "None"])

    pdf.sec("Project-Level Access Control")
    pdf.code(
        "# 3-tier permission dependencies:\n"
        "project_reader    = any project member (or admin)\n"
        "project_contributor = lead_advisor + team_advisor + seller\n"
        "project_manager   = lead_advisor + team_advisor (not seller)\n"
        "\n"
        "# Every project-scoped endpoint checks:\n"
        "1. Is user authenticated? (JWT valid)\n"
        "2. Is user admin? -> bypass all checks\n"
        "3. Is user in ProjectMember table for this project? -> 403 if not\n"
        "4. Does user's global role allow this action? -> 403 if not"
    )

    pdf.sec("Auto-Seeded Admin Users")
    pdf.code(
        "On every startup, init_db() seeds:\n"
        "  ayush@gmail.com / ayush@19 (admin, disclaimer accepted)\n"
        "  aystar@gmail.com / aystar@19 (admin, disclaimer accepted)\n"
        "New registrations default to 'buyer' role (least privileged)"
    )

    # ===== CH3: DMS + OCR =====
    pdf.add_page()
    pdf.ch("3. Document Management + OCR")

    pdf.sec("Upload Flow")
    pdf.code(
        "User uploads file\n"
        "  -> MIME validation (PDF, Word, Excel, CSV, images)\n"
        "  -> Size check (<= 50MB)\n"
        "  -> File saved to disk (uploads/)\n"
        "  -> Document record: status='uploaded'\n"
        "  -> BackgroundTask: _process_document()\n"
        "       -> status='processing'\n"
        "       -> extract_text(bytes, mime, filename)\n"
        "       -> DocumentText created with full content\n"
        "       -> status='ready'\n"
        "       -> On error: status='failed'"
    )

    pdf.sec("OCR Engine (extractor.py)")
    pdf.tr(["Format", "Library", "Method"], hdr=True)
    pdf.tr(["PDF (text)", "pymupdf (fitz)", "page.get_text() per page"])
    pdf.tr(["PDF (scanned)", "pymupdf + pytesseract", "get_pixmap(300dpi) -> OCR"])
    pdf.tr(["Word (.docx)", "python-docx", "Extract paragraphs"])
    pdf.tr(["Excel (.xlsx)", "openpyxl", "Read all sheets, tab-separated"])
    pdf.tr(["CSV/TSV", "pandas", "pd.read_csv() with delimiter"])
    pdf.tr(["Images", "pytesseract + Pillow", "Image.open() -> image_to_string()"])
    pdf.tr(["Plain text", "stdlib", "UTF-8 decode"])

    pdf.sec("Document Chunking for RAG")
    pdf.code(
        "CHUNK_SIZE = 1500 chars (~1 paragraph)\n"
        "CHUNK_OVERLAP = 300 chars (20%)\n"
        "\n"
        "Document text -> sliding window -> chunks stored in document_chunks\n"
        "Each chunk gets a tsvector search_vector (PostgreSQL FTS)\n"
        "GIN index on search_vector for fast full-text queries\n"
        "\n"
        "# Trigger auto-updates search_vector on INSERT/UPDATE:\n"
        "search_vector = to_tsvector('english', chunk_text)"
    )

    # ===== CH4: AI AGENTS =====
    pdf.add_page()
    pdf.ch("4. AI Agent System (RAG + Groq)")

    pdf.sec("Architecture: Template Method Pattern")
    pdf.code(
        "BaseAgent (abstract)\n"
        "  |-- PlanningAgent  (audit scope, document gaps)\n"
        "  |-- LegalAgent     (contracts, IP, litigation)\n"
        "  |-- TaxAgent       (deferred tax, transfer pricing)\n"
        "  |-- FinanceAgent   (EBITDA, revenue, working capital)\n"
        "\n"
        "Each agent implements:\n"
        "  agent_type       -> 'planning' | 'legal' | 'tax' | 'finance'\n"
        "  _build_prompt()  -> (system_prompt, user_prompt)\n"
        "  _mock_findings() -> hardcoded fallback data"
    )

    pdf.sec("RAG Pipeline (FTS-based, no vector embeddings)")
    pdf.code(
        "1. CHUNKING: Document -> 1500-char chunks (300 overlap)\n"
        "2. INDEXING: Each chunk -> tsvector + GIN index in PostgreSQL\n"
        "3. RETRIEVAL: Agent query -> plainto_tsquery() -> ts_rank()\n"
        "   -> Top 10 most relevant chunks returned\n"
        "4. GENERATION: Chunks + system prompt -> Groq API\n"
        "   Model: llama-3.3-70b-versatile\n"
        "   Temperature: 0.1 (near-deterministic)\n"
        "   Max tokens: 8192\n"
        "   Response format: JSON {findings: [...]}\n"
        "5. STORAGE: Findings saved to agent_findings table"
    )

    pdf.sec("Key Difference from Main Branch")
    pdf.p("Main branch used Google Vertex AI (Gemini 1.5 Pro) with pgvector cosine similarity for RAG. Version 1.0 switched to Groq API (Llama 3.3 70B) with PostgreSQL native FTS (tsvector). This eliminates the need for vector embeddings entirely -- simpler architecture, no external embedding service needed.")

    pdf.sec("Anti-Hallucination Rules in Agent Prompts")
    pdf.b("ONLY report findings with concrete evidence from documents")
    pdf.b("Do NOT flag positive statements as risks")
    pdf.b("Do NOT speculate or invent problems")
    pdf.b("Quality over quantity: 3-5 findings maximum")
    pdf.b("Every finding must reference specific document passage")

    pdf.sec("Orchestrator Flow")
    pdf.code(
        "run_analysis(run_id):\n"
        "  1. Set run.status = 'running'\n"
        "  2. Load all 'ready' documents for project\n"
        "  3. For each doc: ensure_document_indexed() (chunk + FTS)\n"
        "  4. For each workstream (sequential):\n"
        "       agent = _AGENTS[workstream]\n"
        "       findings = await agent.analyze(...)\n"
        "       INSERT findings into agent_findings\n"
        "  5. Set run.status = 'completed'\n"
        "  6. On error: status = 'failed', save error_message"
    )

    # ===== CH5: PLANNING =====
    pdf.add_page()
    pdf.ch("5. Planning Module (The USP)")

    pdf.sec("5-Phase Workflow")
    phases = [
        ("Phase 1", "Basic Data", "Advisor enters: company name, legal form, industry, employees, revenue, deal type"),
        ("Phase 2", "Risk Analysis", "AI identifies 5-8 risk areas: legal-form risks, industry risks, deal-type risks"),
        ("Phase 3", "Dialog", "AI asks 5-8 targeted questions: pending litigation? tax structures? key contracts?"),
        ("Phase 4", "Audit Plan", "Structured plan: scope, objectives, workstreams, timeline, resources. Human approves."),
        ("Phase 5", "Request List", "15 items across Legal/Tax/Finance with status + priority tracking"),
    ]
    for phase, name, desc in phases:
        pdf.gold(f"{phase}: {name}", desc)

    pdf.sec("AI Integration")
    pdf.code(
        "# Each phase transition calls Groq API:\n"
        "async _call_groq(system_prompt, user_prompt) -> dict\n"
        "  Model: llama-3.3-70b-versatile\n"
        "  Temperature: 0.2\n"
        "  Max tokens: 4096\n"
        "  Format: JSON object\n"
        "\n"
        "# If no Groq key: returns structured mock data\n"
        "# Mock data is realistic (not placeholder)"
    )

    pdf.sec("Request List Generation")
    pdf.p("15 standard DD items generated from templates, prioritized by identified risks:")
    pdf.b("Legal: Corporate structure chart, shareholder agreements, material contracts, employment contracts, IP register")
    pdf.b("Tax: Tax returns (3-5 years), assessment notices, loss carryforwards, transfer pricing docs")
    pdf.b("Finance: Audited statements (3-5 years), management accounts, EBITDA bridge, working capital analysis")

    # ===== CH6: FINANCE =====
    pdf.add_page()
    pdf.ch("6. Financial Analysis Module")

    pdf.sec("Data Pipeline")
    pdf.code(
        "Upload Excel/CSV\n"
        "  -> pandas.read_csv() or read_excel()\n"
        "  -> Clean column names, replace NaN\n"
        "  -> Store raw_data as JSON in financial_datasets\n"
        "  -> Parse into financial_line_items\n"
        "\n"
        "Variance Analysis:\n"
        "  -> Load all datasets for project\n"
        "  -> Extract numeric columns via pandas\n"
        "  -> Compute: mean, std, min, max, variance_pct\n"
        "  -> Flag 'significant' if variance_pct > 20%\n"
        "  -> Generate follow-up queries for flagged items"
    )

    pdf.sec("Models")
    pdf.tr(["Table", "Key Columns", "Purpose"], hdr=True)
    pdf.tr(["financial_datasets", "raw_data (JSON), chart_of_accounts", "One per uploaded file"])
    pdf.tr(["financial_line_items", "account, period, amount", "Individual data points"])
    pdf.tr(["variance_analyses", "results (JSON), queries (JSON)", "Computed analysis output"])

    # ===== CH7: REPORTS =====
    pdf.add_page()
    pdf.ch("7. Report Generation")

    pdf.sec("3 Report Types")
    pdf.tr(["Type", "Content", "Format"], hdr=True)
    pdf.tr(["Detailed Workstream", "All findings per workstream, grouped by category", "Word .docx"])
    pdf.tr(["Executive Summary", "Critical + high findings only, editable before export", "Word .docx"])
    pdf.tr(["Consolidated", "Cross-workstream summary, grouped by agent type", "Word .docx"])

    pdf.sec("Report Generation Pipeline")
    pdf.code(
        "POST /reports/generate:\n"
        "  1. Fetch ALL completed AgentRun rows for project\n"
        "  2. Load AgentFinding rows from all completed runs\n"
        "  3. Deduplicate findings by title (keep earliest)\n"
        "  4. Filter by workstream (if detailed report)\n"
        "  5. Structure content by report type\n"
        "  6. Append AI Disclaimer to all reports\n"
        "  7. Return Report with JSON content\n"
        "\n"
        "POST /reports/{id}/finalize:\n"
        "  1. python-docx creates Word document\n"
        "  2. Adds title, disclaimer, metadata\n"
        "  3. Iterates content sections\n"
        "  4. Saves to uploads/reports/{uuid}.docx\n"
        "  5. Locks report (is_finalized = True)"
    )

    pdf.sec("AI Disclaimer (Mandatory)")
    pdf.q("Notice: This system uses Artificial Intelligence to support the due diligence review. AI-generated results may be inaccurate, incomplete, or misleading. Responsibility for audit results lies exclusively with the human reviewer.")

    # ===== CH8: AUDIT =====
    pdf.add_page()
    pdf.ch("8. Audit Trail (GDPR Compliance)")

    pdf.sec("Middleware-Based Logging")
    pdf.code(
        "class AuditMiddleware:\n"
        "  # Runs on EVERY API request\n"
        "  # Skips: /health, /docs, /redoc, /favicon.ico\n"
        "  # For each request:\n"
        "  #   1. Extract method, path, status code\n"
        "  #   2. Capture IP address + user-agent\n"
        "  #   3. INSERT into audit_logs (never UPDATE/DELETE)\n"
        "  #   4. Log is immutable (GDPR tamper-proof)"
    )

    pdf.sec("Audit Log Schema")
    pdf.tr(["Column", "Type", "Purpose"], hdr=True)
    pdf.tr(["user_id", "UUID", "Who performed the action"])
    pdf.tr(["action", "Enum", "login, document_uploaded, agent_run_started, etc."])
    pdf.tr(["resource_type", "String", "document, project, user, report"])
    pdf.tr(["resource_id", "String", "UUID of affected resource"])
    pdf.tr(["ip_address", "String", "Client IP (for access tracking)"])
    pdf.tr(["created_at", "DateTime", "Immutable timestamp"])

    # ===== CH9: FRONTEND =====
    pdf.add_page()
    pdf.ch("9. Frontend Architecture")

    pdf.sec("Route Map (14 routes)")
    pdf.code(
        "PUBLIC:\n"
        "  /              -> LandingPage\n"
        "  /login         -> LoginPage\n"
        "  /register      -> RegisterPage\n"
        "  /disclaimer    -> DisclaimerPage\n"
        "\n"
        "PROTECTED (AuthGuard):\n"
        "  /dashboard                       -> DashboardPage\n"
        "  /projects                        -> ProjectsPage\n"
        "  /projects/:id/documents          -> DocumentsPage\n"
        "  /projects/:id/planning           -> PlanningPage\n"
        "  /projects/:id/analysis           -> AgentsPage\n"
        "  /projects/:id/analysis/:runId    -> AgentRunPage\n"
        "  /projects/:id/finance            -> FinancePage\n"
        "  /projects/:id/reports            -> ReportsPage\n"
        "  /projects/:id/red-flags          -> RedFlagsPage\n"
        "  /projects/:id/settings           -> ProjectSettingsPage\n"
        "  /admin/users                     -> AdminUsersPage\n"
        "  /audit                           -> AuditLogsPage\n"
        "  /settings                        -> SettingsPage"
    )

    pdf.sec("Permission Hook (usePermissions)")
    pdf.code(
        "const perms = usePermissions();\n"
        "// Returns:\n"
        "perms.canCreateProject     // admin, lead_advisor\n"
        "perms.canUploadDocuments   // admin, lead, team, seller\n"
        "perms.canRunAnalysis       // admin, lead, team\n"
        "perms.canManageReports     // admin, lead, team\n"
        "perms.onlyFinalizedReports // buyer only\n"
        "perms.isReadOnly           // buyer only\n"
        "perms.canViewAudit         // admin, lead_advisor"
    )

    pdf.sec("State Management")
    pdf.tr(["Tool", "Manages", "Pattern"], hdr=True)
    pdf.tr(["React Query", "Server state (API data)", "Cache + refetch + polling"])
    pdf.tr(["Zustand", "Client state (auth user)", "Global store + localStorage"])
    pdf.tr(["Axios interceptor", "Auth headers + 401 redirect", "Request/response middleware"])

    # ===== CH10: DEPLOYMENT =====
    pdf.add_page()
    pdf.ch("10. Deployment Architecture")

    pdf.sec("Production Target: Google Cloud Run (europe-west3)")
    pdf.tr(["Service", "GCP Product", "Est. Cost/month"], hdr=True)
    pdf.tr(["API", "Cloud Run", "EUR 20-50"])
    pdf.tr(["Frontend", "Cloud Run (static)", "EUR 5-10"])
    pdf.tr(["Database", "Cloud SQL (PostgreSQL 16)", "EUR 30-80"])
    pdf.tr(["Redis", "Memorystore", "EUR 30-50"])
    pdf.tr(["Documents", "Cloud Storage", "EUR 5-20"])
    pdf.tr(["AI", "Groq API (external)", "Pay per token"])
    pdf.tr(["CI/CD", "Cloud Build", "Free tier"])
    pdf.tr(["SSL", "Managed certificates", "Free"])
    pdf.tr(["TOTAL", "", "EUR 100-250"])

    pdf.sec("Security Checklist")
    pdf.b("HTTPS via Cloud Load Balancer + managed SSL")
    pdf.b("Secrets in GCP Secret Manager (not env vars)")
    pdf.b("CORS restricted to production domain only")
    pdf.b("JWT secret: 64-char random string")
    pdf.b("Database: Cloud SQL IAM auth")
    pdf.b("Rate limiting via Cloud Armor")
    pdf.b("Automated backups (Cloud SQL)")
    pdf.b("EU data residency (europe-west3 only)")

    # ===== CH11: WHAT'S MISSING =====
    pdf.add_page()
    pdf.ch("11. What's Missing / Needs Improvement")

    pdf.sec("Critical Gaps")
    pdf.tr(["Issue", "Impact", "Fix Effort"], hdr=True)
    pdf.tr(["Groq fallback is silent", "Users get mock data unknowingly", "2 hours"])
    pdf.tr(["BackgroundTasks not durable", "Tasks lost on restart", "4 hours (Celery)"])
    pdf.tr(["No token blacklist/logout", "Tokens valid until expiry", "3 hours"])
    pdf.tr(["No 2FA/TOTP", "Single-factor auth only", "4 hours"])
    pdf.tr(["No GDPR user deletion", "Compliance gap", "3 hours"])
    pdf.tr(["No password reset", "Users locked out", "3 hours"])
    pdf.tr(["Knowledge module empty", "No cross-project learning", "8 hours"])
    pdf.tr(["Self-improvement empty", "No usage pattern tracking", "8 hours"])
    pdf.tr(["No Alembic migrations", "Schema changes risky", "2 hours"])
    pdf.tr(["Zero automated tests", "No regression safety", "Ongoing"])

    pdf.sec("Features in Main Branch (Not in v1.0)")
    pdf.b("Token blacklist + proper logout")
    pdf.b("2FA/TOTP authentication")
    pdf.b("Password reset flow")
    pdf.b("GDPR user deletion (Art. 17)")
    pdf.b("Settings page (password change + 2FA)")
    pdf.b("Document versioning (version_number + parent_doc_id)")
    pdf.b("Full-text search on documents (tsvector)")
    pdf.b("AI auto-tagging (10 document categories)")
    pdf.b("7-state document lifecycle")
    pdf.b("SKR03/SKR04 chart detection + German number parsing")
    pdf.b("6 Alembic migration files")

    # ===== CH12: NUMBERS =====
    pdf.add_page()
    pdf.ch("12. Numbers to Remember")

    pdf.tr(["Metric", "Value", "Context"], hdr=True)
    nums = [
        ("Modules", "11", "All registered in main.py"),
        ("API Endpoints", "~60+", "Across all modules"),
        ("Database Tables", "17+", "Auth, Projects, DMS, Agent, Finance, Planning, Report, Audit, Knowledge, Self-Improve"),
        ("Docker Services", "5", "PostgreSQL, Redis, API, Celery, Web"),
        ("User Roles", "5", "Admin, Lead Advisor, Team Advisor, Seller, Buyer"),
        ("Agent Types", "4", "Planning, Legal, Tax, Finance"),
        ("Planning Phases", "5", "Basic Data -> Risk -> Dialog -> Plan -> Request List"),
        ("Report Types", "3", "Detailed, Executive Summary, Consolidated"),
        ("Request List Items", "15", "Standard DD checklist across 3 workstreams"),
        ("Chunk Size", "1500 chars", "With 300 char overlap"),
        ("FTS Top-K", "10", "Chunks per agent query"),
        ("LLM Model", "llama-3.3-70b", "Via Groq API"),
        ("LLM Temperature", "0.1 (agents), 0.2 (planning)", "Low for consistency"),
        ("JWT Access Expiry", "60 minutes", "HS256 algorithm"),
        ("JWT Refresh Expiry", "30 days", "For session persistence"),
        ("Max File Size", "50 MB", "Document upload limit"),
        ("Variance Threshold", ">20%", "Flagged as 'significant'"),
        ("Password Hash", "bcrypt", "Deliberately slow (~100ms)"),
    ]
    for n in nums:
        pdf.tr(n)

    pdf.ln(6)
    pdf.sec("Overall Completion")
    pdf.code(
        "Auth + Projects     [====================] 100%\n"
        "DMS + OCR           [====================] 100%\n"
        "AI Agents           [=================   ]  85% (needs Groq key)\n"
        "Planning            [====================] 100%\n"
        "Finance             [====================] 100%\n"
        "Reports             [====================] 100%\n"
        "Audit Trail         [====================] 100%\n"
        "Knowledge           [==                  ]  10% (scaffolded)\n"
        "Self-Improvement    [==                  ]  10% (scaffolded)\n"
        "Deployment/CI       [                    ]   0%\n"
        "\n"
        "OVERALL: ~75% of specification complete"
    )

    # Save
    out = "AI_DD_v1_Study_Guide.pdf"
    pdf.output(out)
    print(f"Generated: {out} ({pdf.page_no()} pages)")


if __name__ == "__main__":
    build()
