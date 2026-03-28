# AI DD — System Architecture Document

**Version:** 2.0 | **Date:** March 2026 | **Status:** CONFIDENTIAL

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Service Catalog](#2-service-catalog)
3. [Monorepo Directory Structure](#3-monorepo-directory-structure)
4. [Infrastructure & Deployment](#4-infrastructure--deployment)
5. [Communication Patterns](#5-communication-patterns)
6. [Database Architecture](#6-database-architecture)
7. [AI Agent Architecture (LangGraph)](#7-ai-agent-architecture-langgraph)
8. [Security & Compliance](#8-security--compliance)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Gap Analysis & Migration Path](#10-gap-analysis--migration-path)
11. [Development Phases](#11-development-phases)

---

## 1. Architecture Overview

### 1.1 System Topology

```
                              ┌─────────────────────────────────────┐
                              │          React Frontend             │
                              │     (Vite + TypeScript + Tailwind)  │
                              │            :5173                    │
                              └──────────────┬──────────────────────┘
                                             │ HTTPS
                                             ▼
                              ┌──────────────────────────────────────┐
                              │          API Gateway Service         │
                              │     (FastAPI — Route & Auth Proxy)   │
                              │              :8000                   │
                              └──────┬───────────────────┬───────────┘
                                     │                   │
                    ┌────────────────┤   REST (sync)     ├────────────────┐
                    │                │                   │                │
         ┌──────── ▼────────┐ ┌─────▼──────┐ ┌─────────▼────┐ ┌────────▼────────┐
         │  Auth Service    │ │  Project   │ │  DMS Service │ │  Agent Service  │
         │  :8001           │ │  Service   │ │  :8003       │ │  (LangGraph)    │
         │                  │ │  :8002     │ │              │ │  :8005          │
         └──────────────────┘ └────────────┘ └──────────────┘ └─────────────────┘

         ┌──────────────────┐ ┌────────────┐ ┌──────────────┐ ┌─────────────────┐
         │  OCR Service     │ │  Planning  │ │  Finance     │ │  Report Service │
         │  :8004           │ │  Service   │ │  Service     │ │  :8008          │
         │                  │ │  :8006     │ │  :8007       │ │                 │
         └──────────────────┘ └────────────┘ └──────────────┘ └─────────────────┘

         ┌──────────────────┐ ┌────────────┐ ┌──────────────┐
         │  Knowledge       │ │  Audit     │ │  Self-       │
         │  Service :8009   │ │  Service   │ │  Improvement │
         │                  │ │  :8010     │ │  Service     │
         └──────────────────┘ └────────────┘ │  :8011       │
                                             └──────────────┘
                    │                   │                   │
                    ▼                   ▼                   ▼
         ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
         │   PostgreSQL 16  │ │   Redis 7        │ │  Google Cloud    │
         │   + pgvector     │ │   (pub/sub +     │ │  (Vertex AI +    │
         │   :5432          │ │    cache)         │ │   GCS)           │
         │                  │ │   :6379          │ │  europe-west3    │
         └──────────────────┘ └──────────────────┘ └──────────────────┘
```

### 1.2 Core Architecture Principles

| # | Principle | Implementation |
|---|-----------|----------------|
| 1 | **Modularity** | 11 independent microservices, each with own API, schema, and Dockerfile |
| 2 | **Human-in-the-Loop** | All AI outputs require approve/reject/modify before external action |
| 3 | **GDPR Compliance** | EU-only data residency (europe-west3), full audit trail, right to deletion |
| 4 | **Anti-Hallucination** | 4-layer RAG architecture — AI only references uploaded documents |
| 5 | **Adaptivity** | Per-project + anonymized cross-project learning |
| 6 | **Professional Design** | Dark, luxurious M&A-grade UI with distinctive typography |
| 7 | **AI Disclaimer** | Mandatory on all AI outputs — humans bear full responsibility |
| 8 | **Phased Development** | 6 phases, each delivering working, testable software |

### 1.3 Port Allocation

| Service | Port | Status |
|---------|------|--------|
| API Gateway | 8000 | To build |
| Auth Service | 8001 | To extract from monolith |
| Project Service | 8002 | To extract from monolith |
| DMS Service | 8003 | To extract from monolith |
| OCR Service | 8004 | To extract from monolith |
| Agent Service (LangGraph) | 8005 | To extract + rewrite |
| Planning Service | 8006 | Not built |
| Finance Service | 8007 | Not built |
| Report Service | 8008 | Not built |
| Knowledge Service | 8009 | Not built |
| Audit Service | 8010 | Not built |
| Self-Improvement Service | 8011 | Not built |
| PostgreSQL | 5432 | Running |
| Redis | 6379 | To add |
| React Frontend | 5173 | Running |

---

## 2. Service Catalog

### 2.1 Auth Service (:8001)

**Responsibility:** User management, roles, permissions, JWT authentication, 2FA

**Current Status:** ~80% built (exists in `apps/api/modules/auth/`)

**API Endpoints:**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/auth/register` | Register new user | Built |
| POST | `/auth/login` | Login, returns access + refresh tokens | Built |
| POST | `/auth/refresh` | Refresh JWT tokens | Built |
| GET | `/auth/me` | Get current user profile | Built |
| POST | `/auth/disclaimer/accept` | Accept platform disclaimer | Built |
| POST | `/auth/2fa/setup` | Initialize 2FA for user | Not built |
| POST | `/auth/2fa/verify` | Verify 2FA code | Not built |
| DELETE | `/auth/users/{id}` | GDPR right-to-deletion | Not built |

**Database Schema: `auth`**
```sql
CREATE SCHEMA auth;

-- auth.users
id              UUID PRIMARY KEY
email           VARCHAR(255) UNIQUE NOT NULL
hashed_password TEXT NOT NULL
full_name       VARCHAR(255) NOT NULL
role            ENUM('admin','lead_advisor','team_advisor','seller','buyer')
is_active       BOOLEAN DEFAULT true
disclaimer_accepted BOOLEAN DEFAULT false
totp_secret     VARCHAR(255)          -- 2FA secret (planned)
created_at      TIMESTAMP
updated_at      TIMESTAMP

-- auth.token_blacklist (planned)
id              UUID PRIMARY KEY
token_jti       VARCHAR(255) UNIQUE   -- JWT ID to revoke
user_id         UUID REFERENCES auth.users
blacklisted_at  TIMESTAMP
expires_at      TIMESTAMP             -- auto-cleanup after expiry
```

**Events Published:**
- `user.created` — when a new user registers
- `user.login` — on successful login (for audit trail)
- `user.deleted` — GDPR deletion event (all services must purge user data)

**Events Subscribed:** None

**Dependencies:** None (root service — no upstream dependencies)

**Gaps to Fix:**
- Add token revocation/blacklist table
- Add 2FA (TOTP) support
- Add GDPR right-to-deletion endpoint
- Publish events to Redis on user actions

---

### 2.2 Project Service (:8002)

**Responsibility:** Deal and project lifecycle management — create, track, close M&A deals

**Current Status:** ~90% built (exists in `apps/api/modules/projects/`)

**API Endpoints:**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/projects` | Create project (advisor role required) | Built |
| GET | `/projects` | List projects (role-filtered) | Built |
| GET | `/projects/{id}` | Get project details | Built |
| PATCH | `/projects/{id}` | Update project | Built |
| POST | `/projects/{id}/members` | Add team member | Built |
| DELETE | `/projects/{id}` | Archive/delete project | Not built |

**Database Schema: `project`**
```sql
CREATE SCHEMA project;

-- project.projects
id              UUID PRIMARY KEY
name            VARCHAR(255) NOT NULL
company_name    VARCHAR(255)
legal_form      ENUM('gmbh','ag','kg','other')
industry        VARCHAR(255)
employee_count  VARCHAR(50)
revenue_size    VARCHAR(100)
registered_office VARCHAR(255)
deal_type       ENUM('share_deal','asset_deal')
status          ENUM('active','on_hold','completed','archived')
description     TEXT
created_by      UUID REFERENCES auth.users
created_at      TIMESTAMP
updated_at      TIMESTAMP

-- project.project_members
id              UUID PRIMARY KEY
project_id      UUID REFERENCES project.projects
user_id         UUID REFERENCES auth.users
added_at        TIMESTAMP
```

**Events Published:**
- `project.created` — triggers audit log entry
- `project.status_changed` — when deal status transitions
- `project.member_added` — for access control propagation

**Events Subscribed:**
- `user.deleted` — remove user from all project memberships

**Dependencies:** Auth Service (user validation)

**Gaps to Fix:**
- Add project deletion/archival endpoint
- Publish events to Redis

---

### 2.3 DMS Service (:8003)

**Responsibility:** Document management — upload, folder structure, versioning, full-text search, status tracking, AI tagging

**Current Status:** ~50% built (exists in `apps/api/modules/dms/`)

**API Endpoints:**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/projects/{id}/documents` | Upload document | Built |
| GET | `/projects/{id}/documents` | List documents | Built |
| GET | `/documents/{id}/text` | Get extracted text | Built |
| GET | `/documents/{id}/download` | Download original file | Built |
| DELETE | `/documents/{id}` | Delete document | Built |
| GET | `/projects/{id}/documents/search` | Full-text search | Not built |
| GET | `/documents/{id}/versions` | List document versions | Not built |
| POST | `/documents/{id}/versions` | Upload new version | Not built |
| PATCH | `/documents/{id}/status` | Update document review status | Not built |
| GET | `/documents/{id}/tags` | Get AI-generated tags | Not built |

**Database Schema: `dms`**
```sql
CREATE SCHEMA dms;

-- dms.documents
id                UUID PRIMARY KEY
project_id        UUID NOT NULL                  -- FK to project.projects
uploaded_by       UUID NOT NULL                  -- FK to auth.users
name              VARCHAR(500) NOT NULL
original_filename VARCHAR(500)
mime_type         VARCHAR(100)
size_bytes        BIGINT
workstream        ENUM('legal','tax','finance','general')
storage_path      TEXT                           -- local path or GCS URI
status            ENUM('requested','uploaded','under_review','reviewed','approved')
page_count        INTEGER
version_number    INTEGER DEFAULT 1              -- NEW: versioning
parent_doc_id     UUID REFERENCES dms.documents  -- NEW: version chain
search_vector     TSVECTOR                       -- NEW: full-text search index
created_at        TIMESTAMP
updated_at        TIMESTAMP

-- dms.document_texts
id              UUID PRIMARY KEY
document_id     UUID UNIQUE REFERENCES dms.documents
content         TEXT
extracted_at    TIMESTAMP

-- dms.document_tags (NEW)
id              UUID PRIMARY KEY
document_id     UUID REFERENCES dms.documents
tag             VARCHAR(100)
confidence      FLOAT                           -- AI tagging confidence 0-1
source          ENUM('ai','manual')
created_at      TIMESTAMP
```

**Events Published:**
- `document.uploaded` — triggers OCR processing
- `document.text_extracted` — text ready for embedding
- `document.status_changed` — status lifecycle transition
- `document.deleted` — cleanup in agent/knowledge services

**Events Subscribed:**
- `ocr.extraction_complete` — update document text and status
- `agent.tags_generated` — store AI-generated tags
- `user.deleted` — anonymize uploaded_by references
- `project.deleted` — cascade delete project documents

**Dependencies:** Auth Service, Project Service, OCR Service

**Gaps to Fix:**
- Change status enum from `uploaded/processing/ready/failed` to `requested/uploaded/under_review/reviewed/approved`
- Add version_number and parent_doc_id for document versioning
- Add document_tags table for AI tagging
- Add tsvector column + GIN index for full-text search
- Add search endpoint
- Add version management endpoints

---

### 2.4 OCR Service (:8004)

**Responsibility:** Extract machine-readable text from all uploaded documents via OCR pipeline

**Current Status:** ~40% built (exists in `apps/api/modules/ocr/`)

**API Endpoints:**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/ocr/extract` | Extract text from document (internal) | Built (as function) |
| GET | `/ocr/status/{job_id}` | Check extraction status | Not built |
| POST | `/ocr/batch` | Batch extract multiple documents | Not built |

**Supported Formats:**
| Format | Engine | Status |
|--------|--------|--------|
| PDF (text-based) | pypdf | Built |
| Word (.docx) | python-docx | Built |
| Excel (.xlsx/.xls) | openpyxl | Built |
| CSV/TSV/TXT | UTF-8 decode | Built |
| PDF (scanned/image) | Google Document AI | Not built |
| Images (JPG, PNG, TIFF) | Google Document AI | Not built |

**Database Schema: `ocr`**
```sql
CREATE SCHEMA ocr;

-- ocr.extraction_jobs
id              UUID PRIMARY KEY
document_id     UUID NOT NULL           -- FK to dms.documents
status          ENUM('queued','processing','completed','failed')
engine_used     VARCHAR(50)             -- 'pypdf', 'python-docx', 'document-ai'
page_count      INTEGER
error_message   TEXT
started_at      TIMESTAMP
completed_at    TIMESTAMP
created_at      TIMESTAMP
```

**Events Published:**
- `ocr.extraction_complete` — text extracted, includes document_id + page_count
- `ocr.extraction_failed` — extraction failed with error details

**Events Subscribed:**
- `document.uploaded` — triggers extraction pipeline

**Dependencies:** DMS Service (document storage access)

**Gaps to Fix:**
- Convert from sync function to standalone service with job queue
- Prepare Google Document AI integration (fallback to local extractors when GCP unavailable)
- Add image-based PDF and image file support
- Add extraction job tracking

---

### 2.5 Agent Service (:8005) — LangGraph

**Responsibility:** Core multi-agent AI system — Orchestrator + 4 specialized workstream agents using LangGraph

**Current Status:** ~50% built (exists in `apps/api/modules/agent/`), needs LangGraph rewrite

**API Endpoints:**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/projects/{id}/agent/runs` | Trigger analysis run | Built |
| GET | `/projects/{id}/agent/runs` | List runs for project | Built |
| GET | `/agent/runs/{run_id}` | Get run details + findings | Built |
| PATCH | `/agent/runs/{run_id}/findings/{id}` | Review finding (approve/reject/modify) | Partial |
| GET | `/agent/runs/{run_id}/status` | Real-time run status | Not built |

**LangGraph Architecture:**

```
                    ┌─────────────────────────┐
                    │     Orchestrator Graph   │
                    │   (LangGraph StateGraph) │
                    └─────────┬───────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼──────┐ ┌─────▼──────┐ ┌──────▼────────┐
     │ Planning Node │ │ Legal Node │ │  Tax Node     │
     │               │ │            │ │               │
     │ - Audit scope │ │ - Contracts│ │ - CIT/VAT     │
     │ - Risk areas  │ │ - IP/labor │ │ - Transfer    │
     │ - Doc gaps    │ │ - CoC      │ │   pricing     │
     └───────────────┘ └────────────┘ └───────────────┘
              │               │               │
              │         ┌─────▼──────┐        │
              │         │Finance Node│        │
              │         │            │        │
              │         │ - EBITDA   │        │
              │         │ - Revenue  │        │
              │         │ - WC/CF    │        │
              │         └────────────┘        │
              │               │               │
              └───────────────┼───────────────┘
                              │
                    ┌─────────▼───────────────┐
                    │   Cross-Check Node      │
                    │  (inter-agent findings)  │
                    └─────────┬───────────────┘
                              │
                    ┌─────────▼───────────────┐
                    │   Consolidation Node    │
                    │  (merge + deduplicate)  │
                    └─────────────────────────┘
```

**LangGraph State Schema:**
```python
class AgentState(TypedDict):
    project_id: str
    documents: list[Document]           # all project documents
    chunks: list[DocumentChunk]         # embedded chunks
    workstreams: list[str]              # selected workstreams
    planning_findings: list[Finding]
    legal_findings: list[Finding]
    tax_findings: list[Finding]
    finance_findings: list[Finding]
    cross_check_alerts: list[Alert]     # inter-agent notifications
    final_findings: list[Finding]       # consolidated output
    run_status: str
    errors: list[str]
```

**Agent Execution Flow:**
1. **Orchestrator** loads all "ready" documents for the project
2. Chunks and embeds documents (idempotent — skips if already done)
3. **Parallel execution** — Planning, Legal, Tax, Finance nodes run concurrently via LangGraph branching
4. **Cross-Check Node** — reviews all findings for cross-workstream implications (e.g., Legal finds change-of-control → notifies Tax about potential implications)
5. **Consolidation Node** — merges, deduplicates, assigns final confidence scores
6. Findings persisted to database

**Anti-Hallucination Design (4 Layers):**

| Layer | Implementation |
|-------|---------------|
| 1. RAG Architecture | All documents chunked (1500 chars, 300 overlap), embedded via `text-embedding-004` (768-dim), stored in pgvector. Cosine similarity retrieval. Every finding includes source_doc_ids + source_excerpts. |
| 2. No-Answer Policy | If retrieved chunks have low relevance (cosine score < 0.3), agent returns `"status": "insufficient_data"` with a list of missing document types. Never speculates. |
| 3. Confidence Scoring | Every finding carries: `confidence` (0.0-1.0), `data_coverage` (percentage of relevant docs analyzed), `missing_evidence` flag (boolean). |
| 4. Structured Prompting | No open-ended chat. Each agent uses workstream-specific structured prompts with evaluation matrices, checklists, and severity rubrics. |

**Database Schema: `agent`**
```sql
CREATE SCHEMA agent;

-- agent.document_chunks
id              UUID PRIMARY KEY
document_id     UUID NOT NULL           -- FK to dms.documents
chunk_index     INTEGER
chunk_text      TEXT
embedding       VECTOR(768)             -- pgvector

-- agent.runs
id              UUID PRIMARY KEY
project_id      UUID NOT NULL           -- FK to project.projects
triggered_by    UUID NOT NULL           -- FK to auth.users
status          ENUM('pending','running','completed','failed')
workstreams     JSONB                   -- ["planning","legal","tax","finance"]
total_documents     INTEGER
processed_documents INTEGER
error_message   TEXT
started_at      TIMESTAMP
completed_at    TIMESTAMP
created_at      TIMESTAMP

-- agent.findings
id              UUID PRIMARY KEY
run_id          UUID REFERENCES agent.runs
agent_type      ENUM('planning','legal','tax','finance')
category        VARCHAR(255)
title           VARCHAR(500)
description     TEXT
severity        ENUM('info','low','medium','high','critical')
confidence      FLOAT                   -- NEW: 0.0-1.0
data_coverage   FLOAT                   -- NEW: % of relevant docs analyzed
missing_evidence BOOLEAN DEFAULT false   -- NEW: flag for incomplete data
source_doc_ids  JSONB                   -- array of document UUIDs
source_excerpts JSONB                   -- array of text snippets with page refs
status          ENUM('pending_review','approved','rejected','modified')
reviewer_id     UUID                    -- FK to auth.users
reviewer_notes  TEXT                    -- NEW: human reviewer comments
reviewed_at     TIMESTAMP
created_at      TIMESTAMP
```

**Events Published:**
- `agent.run_started` — analysis run initiated
- `agent.run_completed` — all findings ready
- `agent.finding_created` — individual finding generated
- `agent.finding_reviewed` — human approved/rejected/modified a finding
- `agent.cross_check_alert` — cross-workstream risk detected

**Events Subscribed:**
- `document.text_extracted` — new document ready for embedding
- `document.deleted` — remove chunks for deleted document
- `project.deleted` — cascade delete all runs and findings

**Dependencies:** Auth, Project, DMS (document access), OCR (text availability)

**Gaps to Fix:**
- Rewrite orchestrator using LangGraph StateGraph
- Add parallel agent execution (LangGraph branching)
- Add Cross-Check Node for inter-agent communication
- Add confidence scoring (confidence, data_coverage, missing_evidence fields)
- Add no-answer policy in agent prompts
- Add "modified" status + reviewer_notes to findings
- Add source citations with page numbers

---

### 2.6 Planning Service (:8006)

**Responsibility:** Interactive 5-phase audit planning, risk analysis dialog, and request list generation

**Current Status:** Not built (the Planning Agent in agent-service handles basic analysis, but the interactive 5-phase workflow does not exist)

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/planning/start` | Initiate audit planning (Phase 1) |
| GET | `/projects/{id}/planning/status` | Get current planning phase |
| POST | `/projects/{id}/planning/risk-analysis` | Trigger AI risk analysis (Phase 2) |
| GET | `/projects/{id}/planning/questions` | Get AI-generated dialog questions (Phase 3) |
| POST | `/projects/{id}/planning/questions/{qid}/answer` | Submit answer to dialog question |
| GET | `/projects/{id}/planning/audit-plan` | Get generated audit plan (Phase 4) |
| PATCH | `/projects/{id}/planning/audit-plan` | Adjust audit plan (human review) |
| POST | `/projects/{id}/planning/audit-plan/approve` | Approve audit plan |
| GET | `/projects/{id}/planning/request-list` | Get request list (Phase 5) |
| PATCH | `/projects/{id}/planning/request-list/{item_id}` | Update request list item |
| GET | `/projects/{id}/planning/request-list/export` | Export as Excel (.xlsx) |

**5-Phase Workflow:**

```
Phase 1              Phase 2              Phase 3              Phase 4              Phase 5
Basic Data      →    AI Risk         →    Interactive     →    Audit Plan      →    Request List
Collection           Analysis              Dialog               Approval             Generation

Company name         Legal-form risks     "Known litigation?"  Human reviews,       Excel export +
Legal form           Industry risks       "Special tax         adjusts, approves    Live web UI
Industry             Location risks        structures?"        plan. Agents only    Per-workstream
Employees                                 "CoC contracts?"     start AFTER          sheets
Revenue                                                        approval.
Deal type
```

**Database Schema: `planning`**
```sql
CREATE SCHEMA planning;

-- planning.audit_plans
id              UUID PRIMARY KEY
project_id      UUID NOT NULL UNIQUE    -- FK to project.projects
phase           ENUM('basic_data','risk_analysis','dialog','approval','request_list','completed')
risk_areas      JSONB                   -- AI-identified risk areas
plan_content    JSONB                   -- structured audit plan
approved_by     UUID                    -- FK to auth.users
approved_at     TIMESTAMP
created_at      TIMESTAMP
updated_at      TIMESTAMP

-- planning.dialog_questions
id              UUID PRIMARY KEY
audit_plan_id   UUID REFERENCES planning.audit_plans
question_text   TEXT NOT NULL
question_type   ENUM('yes_no','text','multi_choice')
options         JSONB                   -- for multi_choice
answer          TEXT
answered_by     UUID                    -- FK to auth.users
answered_at     TIMESTAMP
sort_order      INTEGER
created_at      TIMESTAMP

-- planning.request_list_items
id              UUID PRIMARY KEY
audit_plan_id   UUID REFERENCES planning.audit_plans
workstream      ENUM('legal','tax','finance')
audit_field     VARCHAR(255)
question        TEXT
answer_doc      TEXT                    -- answer text or document reference
status          ENUM('open','partial','query','completed')
priority        ENUM('high','medium','low')
sort_order      INTEGER
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

**Events Published:**
- `planning.phase_changed` — planning workflow advanced
- `planning.plan_approved` — triggers agent service to begin analysis
- `planning.request_list_updated` — item status changed

**Events Subscribed:**
- `project.created` — initialize blank audit plan
- `agent.finding_created` — dynamically adapt plan based on new findings

**Dependencies:** Auth, Project, Agent Service (for AI risk analysis)

---

### 2.7 Finance Service (:8007)

**Responsibility:** Financial data import, account mapping, variance analysis (internal + external benchmarks)

**Current Status:** Not built

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/finance/import` | Import financial data (Excel/TSV) |
| GET | `/projects/{id}/finance/data` | Get imported financial data |
| POST | `/projects/{id}/finance/data/append` | Append new monthly data |
| GET | `/projects/{id}/finance/variance/internal` | Internal historical analysis |
| GET | `/projects/{id}/finance/variance/external` | External benchmark analysis |
| GET | `/projects/{id}/finance/queries` | AI-generated follow-up queries |
| PATCH | `/projects/{id}/finance/queries/{qid}` | Approve/reject query (HITL) |

**Database Schema: `finance`**
```sql
CREATE SCHEMA finance;

-- finance.datasets
id              UUID PRIMARY KEY
project_id      UUID NOT NULL           -- FK to project.projects
chart_of_accounts ENUM('skr03','skr04','custom')
import_source   VARCHAR(255)            -- filename
imported_by     UUID                    -- FK to auth.users
created_at      TIMESTAMP

-- finance.line_items
id              UUID PRIMARY KEY
dataset_id      UUID REFERENCES finance.datasets
account_code    VARCHAR(20)
account_name    VARCHAR(255)
period          DATE                    -- YYYY-MM-01
amount          DECIMAL(15,2)
currency        VARCHAR(3) DEFAULT 'EUR'

-- finance.variance_results
id              UUID PRIMARY KEY
project_id      UUID NOT NULL
analysis_type   ENUM('mom','yoy','trend','benchmark')
line_item_id    UUID REFERENCES finance.line_items
variance_pct    FLOAT
variance_abs    DECIMAL(15,2)
significance    ENUM('normal','notable','significant','critical')
ai_commentary   TEXT
created_at      TIMESTAMP

-- finance.generated_queries
id              UUID PRIMARY KEY
project_id      UUID NOT NULL
variance_id     UUID REFERENCES finance.variance_results
question        TEXT
status          ENUM('pending_review','approved','rejected')
approved_by     UUID
created_at      TIMESTAMP
```

**Events Published:**
- `finance.data_imported` — new financial data available
- `finance.variance_detected` — significant variance found
- `finance.query_approved` — approved query added to request list

**Events Subscribed:**
- `planning.plan_approved` — begin financial analysis
- `project.deleted` — cascade delete financial data

**Dependencies:** Auth, Project, Planning Service (for approved plan scope)

---

### 2.8 Report Service (:8008)

**Responsibility:** Generate Word (.docx) reports and Excel (.xlsx) request lists

**Current Status:** Not built

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/reports/detailed/{workstream}` | Generate detailed workstream report |
| POST | `/projects/{id}/reports/executive-summary` | Generate executive summary |
| POST | `/projects/{id}/reports/consolidated` | Generate consolidated overall report |
| GET | `/projects/{id}/reports` | List generated reports |
| GET | `/reports/{id}/download` | Download report file |
| GET | `/reports/{id}/preview` | Preview report in web (JSON structure) |
| PATCH | `/reports/{id}/sections/{section_id}` | Edit section before export (HITL) |
| POST | `/projects/{id}/reports/request-list/export` | Export request list as Excel |

**Report Types:**

| Type | Contents | Format |
|------|----------|--------|
| Detailed Workstream | All findings per workstream, risk classification, recommended actions, source appendix | Word (.docx) |
| Executive Summary | Condensed overview, editable in web before export | Word (.docx) |
| Consolidated Overall | Cross-workstream summary, deal-breaker analysis, overall risk | Word (.docx) |
| Request List | Per-workstream sheets, status/priority dropdowns | Excel (.xlsx) |

All reports include: logo placeholder, source citations, confidence levels, timestamps, AI disclaimer.

**Database Schema: `report`**
```sql
CREATE SCHEMA report;

-- report.reports
id              UUID PRIMARY KEY
project_id      UUID NOT NULL
report_type     ENUM('detailed_legal','detailed_tax','detailed_finance','executive_summary','consolidated')
title           VARCHAR(500)
generated_by    UUID                    -- FK to auth.users
storage_path    TEXT                    -- path to generated .docx file
content_json    JSONB                   -- structured content for web preview/editing
status          ENUM('generating','draft','review','finalized')
finalized_by    UUID
finalized_at    TIMESTAMP
created_at      TIMESTAMP

-- report.report_sections
id              UUID PRIMARY KEY
report_id       UUID REFERENCES report.reports
section_key     VARCHAR(100)
title           VARCHAR(255)
content         TEXT                    -- editable content
sort_order      INTEGER
edited_by       UUID
edited_at       TIMESTAMP
```

**Events Published:**
- `report.generated` — report ready for review
- `report.finalized` — report approved and locked

**Events Subscribed:**
- `agent.run_completed` — auto-generate draft reports
- `planning.request_list_updated` — regenerate Excel export

**Dependencies:** Auth, Project, Agent Service (findings), Planning Service (request list), Finance Service (financial data)

---

### 2.9 Knowledge Service (:8009)

**Responsibility:** Per-project learning file + anonymized cross-project knowledge base

**Current Status:** Not built

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{id}/knowledge` | Get project learning file |
| GET | `/knowledge/patterns` | Get cross-project risk patterns |
| POST | `/knowledge/sources` | Add external knowledge source (admin) |
| GET | `/knowledge/sources` | List knowledge sources |

**Database Schema: `knowledge`**
```sql
CREATE SCHEMA knowledge;

-- knowledge.project_learnings
id              UUID PRIMARY KEY
project_id      UUID NOT NULL
finding_summary TEXT
risk_category   VARCHAR(255)
industry        VARCHAR(255)
legal_form      VARCHAR(50)
severity        VARCHAR(20)
created_at      TIMESTAMP

-- knowledge.cross_project_patterns (anonymized)
id              UUID PRIMARY KEY
industry        VARCHAR(255)
legal_form      VARCHAR(50)
risk_category   VARCHAR(255)
occurrence_pct  FLOAT                   -- "occurs in X% of cases"
avg_severity    VARCHAR(20)
sample_size     INTEGER
last_updated    TIMESTAMP

-- knowledge.external_sources
id              UUID PRIMARY KEY
name            VARCHAR(255)
description     TEXT
source_type     ENUM('legal_reference','regulatory','benchmark')
content         TEXT
uploaded_by     UUID
created_at      TIMESTAMP
```

**Anonymization Rules:**
| Removed | Retained |
|---------|----------|
| Company names | Numerical values and key metrics |
| Personal names | Risk patterns per industry type |
| Addresses and locations | Legal-form-related findings |
| All directly identifying info | Typical issues and their frequency |

**Events Subscribed:**
- `agent.finding_reviewed` — when findings are approved, anonymize and store for cross-project learning
- `project.status_changed` (to "completed") — finalize project learning file

**Dependencies:** Auth, Agent Service (approved findings)

---

### 2.10 Audit Service (:8010)

**Responsibility:** Full GDPR-compliant audit trail logging + compliance tracking

**Current Status:** Not built

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit/logs` | Query audit logs (admin only, filterable) |
| GET | `/audit/logs/export` | Export logs as Excel/PDF |
| GET | `/audit/users/{id}/activity` | User activity history |
| GET | `/audit/documents/{id}/access` | Document access log |
| GET | `/audit/compliance/status` | GDPR compliance dashboard |

**Database Schema: `audit`**
```sql
CREATE SCHEMA audit;

-- audit.logs (append-only, tamper-proof)
id              UUID PRIMARY KEY
event_type      VARCHAR(100) NOT NULL   -- e.g., 'document.viewed', 'finding.approved'
actor_id        UUID                    -- FK to auth.users (NULL for system events)
actor_email     VARCHAR(255)            -- denormalized for tamper-proof record
resource_type   VARCHAR(100)            -- 'document', 'finding', 'project', etc.
resource_id     UUID
project_id      UUID                    -- FK to project.projects (for filtering)
details         JSONB                   -- event-specific metadata
ip_address      INET
user_agent      TEXT
created_at      TIMESTAMP NOT NULL DEFAULT NOW()

-- NO UPDATE OR DELETE operations allowed on this table
-- Enforced via database triggers + application-level checks
```

**Logged Events (from spec §5.2):**
- Document viewed, downloaded, uploaded
- Permission changed
- User invited / access revoked
- Login / logout
- Failed access attempts
- Finding reviewed (approved/rejected/modified)
- Report generated / finalized
- Audit plan approved
- Any data deletion (GDPR)

**Events Subscribed:** ALL events from ALL services — the Audit Service is a universal subscriber.

**Dependencies:** None (receives events only, no outbound calls)

---

### 2.11 Self-Improvement Service (:8011)

**Responsibility:** Observe usage patterns and generate concrete code improvement suggestions

**Current Status:** Not built (Phase 6 — lowest priority)

**Database Schema: `self_improve`**
```sql
CREATE SCHEMA self_improve;

-- self_improve.usage_patterns
id              UUID PRIMARY KEY
pattern_type    ENUM('manual_correction','adjusted_suggestion','performance_bottleneck')
module          VARCHAR(100)
description     TEXT
frequency       INTEGER
first_seen      TIMESTAMP
last_seen       TIMESTAMP

-- self_improve.suggestions
id              UUID PRIMARY KEY
pattern_id      UUID REFERENCES self_improve.usage_patterns
title           VARCHAR(255)
rationale       TEXT
proposed_change TEXT
expected_benefit TEXT
status          ENUM('proposed','approved','rejected','implemented')
reviewed_by     UUID
created_at      TIMESTAMP
```

**Events Subscribed:**
- `agent.finding_reviewed` — track manual corrections to AI findings
- `report.section_edited` — track adjustments to AI-generated content

---

## 3. Monorepo Directory Structure

```
AI DD/
│
├── services/
│   ├── auth/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # FastAPI app for auth service
│   │   │   ├── config.py            # Service-specific settings
│   │   │   ├── models.py            # SQLAlchemy models (auth schema)
│   │   │   ├── schemas.py           # Pydantic request/response schemas
│   │   │   ├── router.py            # API endpoints
│   │   │   ├── service.py           # Business logic
│   │   │   └── dependencies.py      # FastAPI dependencies
│   │   ├── migrations/
│   │   │   ├── alembic.ini
│   │   │   └── versions/            # Alembic migration files
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── project/                     # Same structure as auth/
│   ├── dms/
│   ├── ocr/
│   ├── agent/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── router.py
│   │   │   ├── graphs/              # LangGraph definitions
│   │   │   │   ├── orchestrator.py  # Main StateGraph
│   │   │   │   ├── planning_node.py
│   │   │   │   ├── legal_node.py
│   │   │   │   ├── tax_node.py
│   │   │   │   ├── finance_node.py
│   │   │   │   ├── cross_check.py
│   │   │   │   └── consolidation.py
│   │   │   ├── rag/
│   │   │   │   ├── embeddings.py    # Chunking + embedding logic
│   │   │   │   └── retrieval.py     # pgvector similarity search
│   │   │   └── prompts/
│   │   │       ├── planning.py      # Structured prompts
│   │   │       ├── legal.py
│   │   │       ├── tax.py
│   │   │       └── finance.py
│   │   ├── Dockerfile
│   │   └── requirements.txt         # Includes langgraph, langchain-google-vertexai
│   │
│   ├── planning/
│   ├── finance/
│   ├── report/
│   ├── knowledge/
│   ├── audit/
│   └── self-improve/
│
├── gateway/
│   ├── app/
│   │   ├── main.py                  # API Gateway — route proxying
│   │   ├── config.py                # Service registry (URLs + ports)
│   │   ├── middleware/
│   │   │   ├── auth.py              # JWT validation middleware
│   │   │   ├── cors.py              # CORS configuration
│   │   │   ├── audit.py             # Request logging → audit service
│   │   │   └── rate_limit.py        # Rate limiting
│   │   └── routes.py                # Route definitions → service mapping
│   ├── Dockerfile
│   └── requirements.txt
│
├── shared/
│   ├── aidd_shared/
│   │   ├── __init__.py
│   │   ├── database.py              # Base DB engine factory, schema helpers
│   │   ├── auth.py                  # JWT decode helper for service-to-service auth
│   │   ├── events.py                # Redis pub/sub client (publish/subscribe helpers)
│   │   ├── models.py                # Shared base model (UUID PK, timestamps)
│   │   ├── schemas.py               # Common Pydantic schemas (pagination, errors)
│   │   └── config.py                # Shared config base class
│   ├── setup.py                     # pip install -e ../shared
│   └── requirements.txt
│
├── apps/
│   └── web/                         # React frontend (unchanged)
│       ├── src/
│       │   ├── api/                 # API client modules (all hit gateway :8000)
│       │   ├── pages/
│       │   ├── components/
│       │   ├── store/
│       │   └── types/
│       ├── package.json
│       └── vite.config.ts
│
├── infrastructure/
│   └── docker/
│       ├── gateway.Dockerfile
│       └── service.Dockerfile       # Generic service Dockerfile (parameterized)
│
├── docker-compose.yml               # All services + PostgreSQL + Redis
├── docker-compose.dev.yml           # Dev overrides (hot reload, volumes)
├── .env.example
├── package.json                     # Root monorepo (web dev scripts)
│
└── docs/
    └── SYSTEM_ARCHITECTURE.md       # THIS DOCUMENT
```

---

## 4. Infrastructure & Deployment

### 4.1 Docker Compose (Development)

```yaml
# docker-compose.yml — 11 services + gateway + PostgreSQL + Redis + Frontend

services:
  # --- Data Stores ---
  db:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: aidd
      POSTGRES_PASSWORD: aidd_dev_pass
      POSTGRES_DB: aidd
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infrastructure/init-schemas.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: pg_isready -U aidd
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: redis-cli ping
      interval: 5s

  # --- API Gateway ---
  gateway:
    build: { context: ./gateway, dockerfile: Dockerfile }
    ports: ["8000:8000"]
    environment:
      AUTH_SERVICE_URL: http://auth:8001
      PROJECT_SERVICE_URL: http://project:8002
      DMS_SERVICE_URL: http://dms:8003
      OCR_SERVICE_URL: http://ocr:8004
      AGENT_SERVICE_URL: http://agent:8005
      PLANNING_SERVICE_URL: http://planning:8006
      FINANCE_SERVICE_URL: http://finance:8007
      REPORT_SERVICE_URL: http://report:8008
      KNOWLEDGE_SERVICE_URL: http://knowledge:8009
      AUDIT_SERVICE_URL: http://audit:8010
      REDIS_URL: redis://redis:6379
    depends_on: [redis]

  # --- Core Services ---
  auth:
    build: { context: ./services/auth, dockerfile: Dockerfile }
    ports: ["8001:8001"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: auth
      REDIS_URL: redis://redis:6379
      SECRET_KEY: dev-secret-change-in-prod-32chars!!
    depends_on: [db, redis]

  project:
    build: { context: ./services/project, dockerfile: Dockerfile }
    ports: ["8002:8002"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: project
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  dms:
    build: { context: ./services/dms, dockerfile: Dockerfile }
    ports: ["8003:8003"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: dms
      REDIS_URL: redis://redis:6379
      STORAGE_PATH: /app/uploads
    volumes:
      - uploads:/app/uploads
    depends_on: [db, redis]

  ocr:
    build: { context: ./services/ocr, dockerfile: Dockerfile }
    ports: ["8004:8004"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: ocr
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  agent:
    build: { context: ./services/agent, dockerfile: Dockerfile }
    ports: ["8005:8005"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: agent
      REDIS_URL: redis://redis:6379
      VERTEX_AI_LOCATION: europe-west3
      GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:-}
    depends_on: [db, redis]

  planning:
    build: { context: ./services/planning, dockerfile: Dockerfile }
    ports: ["8006:8006"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: planning
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  finance:
    build: { context: ./services/finance, dockerfile: Dockerfile }
    ports: ["8007:8007"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: finance
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  report:
    build: { context: ./services/report, dockerfile: Dockerfile }
    ports: ["8008:8008"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: report
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  knowledge:
    build: { context: ./services/knowledge, dockerfile: Dockerfile }
    ports: ["8009:8009"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: knowledge
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  audit:
    build: { context: ./services/audit, dockerfile: Dockerfile }
    ports: ["8010:8010"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: audit
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  self-improve:
    build: { context: ./services/self-improve, dockerfile: Dockerfile }
    ports: ["8011:8011"]
    environment:
      DATABASE_URL: postgresql+psycopg://aidd:aidd_dev_pass@db:5432/aidd
      DB_SCHEMA: self_improve
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]

  # --- Frontend ---
  web:
    build: { context: ./apps/web, dockerfile: ../../infrastructure/docker/web.Dockerfile }
    ports: ["5173:5173"]
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  pgdata:
  uploads:
```

### 4.2 Database Schema Initialization

```sql
-- infrastructure/init-schemas.sql
-- Executed on first PostgreSQL startup

CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- trigram index for full-text search

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS project;
CREATE SCHEMA IF NOT EXISTS dms;
CREATE SCHEMA IF NOT EXISTS ocr;
CREATE SCHEMA IF NOT EXISTS agent;
CREATE SCHEMA IF NOT EXISTS planning;
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS report;
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS self_improve;
```

### 4.3 Shared Library Installation

Each service's `requirements.txt` includes:
```
-e ../../shared    # Install shared library in editable mode
```

This gives every service access to `aidd_shared.events`, `aidd_shared.database`, `aidd_shared.auth`, etc.

### 4.4 Alembic Per-Service

Each service has its own Alembic configuration targeting its schema:
```ini
# services/auth/migrations/alembic.ini
[alembic]
script_location = versions
sqlalchemy.url = %(DATABASE_URL)s

[alembic:env]
target_metadata = app.models.Base.metadata
version_table_schema = auth
```

---

## 5. Communication Patterns

### 5.1 Sync: REST via API Gateway

The frontend sends all requests to the **API Gateway** (:8000), which:
1. Validates JWT token (via shared auth middleware)
2. Routes the request to the appropriate service based on URL prefix
3. Forwards the response back to the client

**Route Mapping:**
```
/api/v1/auth/*        → Auth Service      :8001
/api/v1/projects/*    → Project Service   :8002
/api/v1/documents/*   → DMS Service       :8003
/api/v1/ocr/*         → OCR Service       :8004
/api/v1/agent/*       → Agent Service     :8005
/api/v1/planning/*    → Planning Service  :8006
/api/v1/finance/*     → Finance Service   :8007
/api/v1/reports/*     → Report Service    :8008
/api/v1/knowledge/*   → Knowledge Service :8009
/api/v1/audit/*       → Audit Service     :8010
```

### 5.2 Async: Redis Pub/Sub Event Bus

Services communicate asynchronously via Redis pub/sub channels. All events follow a standardized schema:

**Event Envelope:**
```json
{
  "event_id": "uuid",
  "event_type": "document.uploaded",
  "timestamp": "2026-03-27T14:30:00Z",
  "source_service": "dms",
  "actor_id": "user-uuid",
  "project_id": "project-uuid",
  "payload": {
    "document_id": "doc-uuid",
    "workstream": "legal",
    "mime_type": "application/pdf"
  }
}
```

### 5.3 Event Catalog

| Event | Publisher | Subscribers | Trigger |
|-------|-----------|-------------|---------|
| `user.created` | Auth | Audit | New user registration |
| `user.login` | Auth | Audit | Successful login |
| `user.deleted` | Auth | All services | GDPR deletion request |
| `project.created` | Project | Planning, Audit | New project created |
| `project.status_changed` | Project | Knowledge, Audit | Deal status transition |
| `project.member_added` | Project | Audit | Team member added |
| `document.uploaded` | DMS | OCR, Audit | New document uploaded |
| `document.status_changed` | DMS | Audit | Review status change |
| `document.deleted` | DMS | Agent, Audit | Document removed |
| `ocr.extraction_complete` | OCR | DMS, Agent | Text extracted |
| `ocr.extraction_failed` | OCR | DMS, Audit | Extraction error |
| `agent.run_started` | Agent | Audit | Analysis triggered |
| `agent.run_completed` | Agent | Report, Audit | All findings ready |
| `agent.finding_created` | Agent | Planning, Audit | New finding |
| `agent.finding_reviewed` | Agent | Knowledge, Audit | Finding approved/rejected |
| `agent.cross_check_alert` | Agent | Audit | Cross-workstream risk |
| `planning.phase_changed` | Planning | Audit | Planning phase advance |
| `planning.plan_approved` | Planning | Agent, Audit | Triggers agent analysis |
| `planning.request_list_updated` | Planning | Report, Audit | Item status changed |
| `finance.data_imported` | Finance | Audit | Financial data added |
| `finance.variance_detected` | Finance | Audit | Significant variance |
| `finance.query_approved` | Finance | Planning, Audit | Query added to request list |
| `report.generated` | Report | Audit | Report draft ready |
| `report.finalized` | Report | Audit | Report locked |

### 5.4 Shared Event Bus Client

```python
# shared/aidd_shared/events.py

import json
import redis.asyncio as redis
from datetime import datetime, timezone
from uuid import uuid4

class EventBus:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    async def publish(self, event_type: str, payload: dict,
                      actor_id: str = None, project_id: str = None,
                      source_service: str = "unknown"):
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_service": source_service,
            "actor_id": actor_id,
            "project_id": project_id,
            "payload": payload,
        }
        channel = event_type.split(".")[0]  # e.g., "document" from "document.uploaded"
        await self.redis.publish(channel, json.dumps(event))

    async def subscribe(self, *channels: str, handler):
        await self.pubsub.subscribe(*channels)
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                await handler(event)
```

---

## 6. Database Architecture

### 6.1 Schema Isolation Model

```
PostgreSQL Instance (aidd)
│
├── Schema: auth          ← Auth Service owns this
│   ├── users
│   └── token_blacklist
│
├── Schema: project       ← Project Service owns this
│   ├── projects
│   └── project_members
│
├── Schema: dms           ← DMS Service owns this
│   ├── documents
│   ├── document_texts
│   └── document_tags
│
├── Schema: ocr           ← OCR Service owns this
│   └── extraction_jobs
│
├── Schema: agent         ← Agent Service owns this
│   ├── document_chunks   (with pgvector embeddings)
│   ├── runs
│   └── findings
│
├── Schema: planning      ← Planning Service owns this
│   ├── audit_plans
│   ├── dialog_questions
│   └── request_list_items
│
├── Schema: finance       ← Finance Service owns this
│   ├── datasets
│   ├── line_items
│   ├── variance_results
│   └── generated_queries
│
├── Schema: report        ← Report Service owns this
│   ├── reports
│   └── report_sections
│
├── Schema: knowledge     ← Knowledge Service owns this
│   ├── project_learnings
│   ├── cross_project_patterns
│   └── external_sources
│
├── Schema: audit         ← Audit Service owns this
│   └── logs              (append-only)
│
└── Schema: self_improve  ← Self-Improvement Service owns this
    ├── usage_patterns
    └── suggestions
```

### 6.2 Cross-Schema References

Services reference other schemas' IDs (e.g., `dms.documents.project_id` references `project.projects.id`) but do **NOT** use foreign key constraints across schemas. Referential integrity across services is maintained via:
1. **Events** — deletion events trigger cascade cleanup
2. **Eventual consistency** — services handle missing references gracefully
3. **Gateway validation** — the API gateway validates resource existence before forwarding

---

## 7. AI Agent Architecture (LangGraph)

### 7.1 Technology Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | LangGraph (from LangChain) |
| LLM | Google Vertex AI — Gemini 1.5 Pro |
| Embeddings | text-embedding-004 (768 dimensions) |
| Vector Store | PostgreSQL + pgvector |
| Region | europe-west3 (Frankfurt) — EU only |

### 7.2 LangGraph Orchestrator Graph

```python
from langgraph.graph import StateGraph, END

# Define the orchestrator as a StateGraph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("load_documents", load_documents_node)
graph.add_node("embed_documents", embed_documents_node)
graph.add_node("planning_agent", planning_agent_node)
graph.add_node("legal_agent", legal_agent_node)
graph.add_node("tax_agent", tax_agent_node)
graph.add_node("finance_agent", finance_agent_node)
graph.add_node("cross_check", cross_check_node)
graph.add_node("consolidate", consolidation_node)

# Define edges
graph.set_entry_point("load_documents")
graph.add_edge("load_documents", "embed_documents")

# Parallel branching — all 4 agents run concurrently
graph.add_edge("embed_documents", "planning_agent")
graph.add_edge("embed_documents", "legal_agent")
graph.add_edge("embed_documents", "tax_agent")
graph.add_edge("embed_documents", "finance_agent")

# All agents converge at cross-check
graph.add_edge("planning_agent", "cross_check")
graph.add_edge("legal_agent", "cross_check")
graph.add_edge("tax_agent", "cross_check")
graph.add_edge("finance_agent", "cross_check")

# Cross-check → Consolidation → END
graph.add_edge("cross_check", "consolidate")
graph.add_edge("consolidate", END)

orchestrator = graph.compile()
```

### 7.3 RAG Pipeline

```
Document Upload → Text Extraction (OCR) → Chunking → Embedding → pgvector Storage
                                              │
                                    1500 chars, 300 overlap
                                              │
                                    text-embedding-004 (768-dim)
                                              │
                            ┌─────────────────▼──────────────────┐
                            │   pgvector (agent.document_chunks)  │
                            │   Cosine similarity search          │
                            │   Top-K retrieval per query         │
                            └─────────────────────────────────────┘
                                              │
                            Agent query → Retrieve relevant chunks
                                              │
                            Construct prompt with source citations
                                              │
                            Gemini 1.5 Pro generates findings
                                              │
                            Finding includes: confidence, sources, excerpts
```

### 7.4 Cross-Agent Communication

When an agent detects a cross-workstream implication:

1. **Legal Agent** finds a change-of-control clause → publishes `agent.cross_check_alert` with `{ "from": "legal", "to": "tax", "alert": "Change-of-control clause found in Contract X — may trigger tax implications under §8c KStG" }`
2. The **Cross-Check Node** in LangGraph collects all alerts and injects them into the relevant agent's context
3. If running in real-time, alerts are also published to Redis for the Audit Service to log

### 7.5 Finding Schema

Every AI-generated finding follows this structure:
```json
{
  "agent_type": "legal",
  "category": "Change of Control",
  "title": "Key supplier contract contains CoC clause",
  "description": "The framework agreement with Supplier AG (§12.3) contains...",
  "severity": "high",
  "confidence": 0.87,
  "data_coverage": 0.92,
  "missing_evidence": false,
  "source_doc_ids": ["uuid-1", "uuid-2"],
  "source_excerpts": [
    {"doc_id": "uuid-1", "page": 14, "text": "In the event of a change..."},
    {"doc_id": "uuid-2", "page": 3, "text": "Subject to §12.3..."}
  ],
  "status": "pending_review"
}
```

---

## 8. Security & Compliance

### 8.1 Authentication Flow

```
Client → Gateway (:8000) → JWT Validation → Route to Service
                               │
                      ┌────────▼────────┐
                      │ Decode JWT      │
                      │ Check expiry    │
                      │ Check blacklist │
                      │ Extract user_id │
                      │ + role          │
                      └────────┬────────┘
                               │
                      Forward request with
                      X-User-ID and X-User-Role
                      headers to target service
```

### 8.2 Role-Based Access Control

| Role | Projects | Documents | Agent Runs | Reports | Admin Panel |
|------|----------|-----------|------------|---------|-------------|
| Admin | Full CRUD | Full CRUD | Trigger + Review | Generate + Finalize | Full access |
| M&A Lead Advisor | Create + Manage | Full CRUD | Trigger + Review | Generate + Finalize | Read audit logs |
| M&A Team Advisor | View assigned | Upload + View assigned | Trigger + View | View drafts | None |
| Seller | View own | Upload to assigned | None | None | None |
| Buyer/Investor | View approved | View approved docs | None | View finalized only | None |

### 8.3 VDR Security Features (Roadmap)

| Feature | Description | Priority |
|---------|-------------|----------|
| Granular Permissions | Per-user, per-folder, per-document (Read/Download/Upload/Print/Rename/Delete/Share) | High |
| Dynamic Watermarks | Viewer's name + email + timestamp overlaid on document preview | High |
| Admin Activity Log | Tamper-proof log of all VDR interactions (viewable, exportable) | High |
| Access Expiry | Time-limited permissions with auto-revocation | Medium |
| NDA Gate | Digital NDA acceptance required before dataroom access | Medium |
| Fence View Mode | Blur/redact sensitive sections for specific users | Low |
| 2FA | TOTP-based two-factor authentication (enforced for external users) | Medium |

### 8.4 GDPR Compliance

| Requirement | Implementation |
|-------------|----------------|
| Data Residency | All data on EU servers — PostgreSQL + GCS + Vertex AI in europe-west3 |
| Encryption at Rest | GCS server-side encryption (Google-managed or CMEK) |
| Encryption in Transit | TLS on all API and inter-service communication |
| Audit Trail | Every data access logged in audit.logs (append-only, tamper-proof) |
| Right to Deletion | `user.deleted` event triggers cascade purge across all services |
| Data Processing Register | Maintained automatically by audit service |
| Anonymization | Cross-project learning uses only anonymized data — no PII retained |
| Cookie & Privacy | Cookie consent and privacy policy built into frontend |

### 8.5 AI Disclaimer

The following disclaimer is mandatory on all AI-generated content:

> *Notice: This system uses Artificial Intelligence to support the due diligence review. AI-generated results may be inaccurate, incomplete, or misleading. Responsibility for audit results, their interpretation, and all decisions derived therefrom lies exclusively with the human reviewer. This tool does not replace qualified legal, tax, or financial advisory services.*

**Display locations:**
- Every AI-generated report
- Every AI-generated query/recommendation
- Web interface footer
- One-time confirmation required on first login

---

## 9. Frontend Architecture

### 9.1 Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | React 19 + TypeScript |
| Build Tool | Vite 8 |
| Styling | Tailwind CSS + shadcn/ui |
| State | Zustand (auth) + React Query (server state) |
| Router | react-router-dom v7 |
| Icons | lucide-react |
| Typography | DM Serif Display (display) + DM Sans (body) + JetBrains Mono (code) |

### 9.2 Design System

- **Color Scheme:** Dark navy base (#0a0d14) with gold accents
- **Philosophy:** Professional, luxurious, M&A-grade — no generic AI aesthetics
- **Responsive:** Desktop and tablet optimized
- **Animations:** Subtle page transitions and micro-interactions

### 9.3 Page Map

```
/                              → Landing Page
/login                         → Login
/register                      → Registration
/disclaimer                    → Disclaimer Acceptance

/dashboard                     → KPI Dashboard (risk score, red flags, module status)
/projects                      → Project List + Create
/projects/:id                  → Project Detail
/projects/:id/documents        → Document Management (upload, search, versions)
/projects/:id/planning         → 5-Phase Audit Planning UI
/projects/:id/planning/request-list → Request List (editable web UI)
/projects/:id/analysis         → Agent Runs List
/projects/:id/analysis/:runId  → Run Detail + Finding Review (approve/reject/modify)
/projects/:id/finance          → Financial Data + Variance Analysis
/projects/:id/reports          → Report Generation + Preview + Export
/projects/:id/dataroom         → Transaction Dataroom (VDR)
/admin/audit                   → Audit Logs (admin only)
/admin/knowledge               → Knowledge Base Management (admin only)
/settings                      → User Settings
```

### 9.4 Frontend → Gateway Communication

The frontend communicates exclusively with the API Gateway at `:8000`. The Vite dev proxy forwards `/api/*` requests:

```typescript
// vite.config.ts
proxy: {
  "/api": {
    target: "http://localhost:8000",
    changeOrigin: true,
  },
},
```

---

## 10. Gap Analysis & Migration Path

### 10.1 Module Gap Summary

| Module | Current | Target | Key Gaps |
|--------|---------|--------|----------|
| Auth | 80% | 100% | 2FA, token blacklist, GDPR deletion |
| Project | 90% | 100% | Deletion endpoint, event publishing |
| DMS | 50% | 100% | Versioning, AI tagging, status lifecycle, full-text search |
| OCR | 40% | 100% | Google Document AI, image OCR, job tracking |
| Agent | 50% | 100% | LangGraph rewrite, confidence scores, cross-comm, parallel exec |
| Planning | 0% | 100% | Entire 5-phase workflow |
| Finance | 0% | 100% | Data import, variance analysis |
| Report | 0% | 100% | Word/Excel generation |
| Knowledge | 0% | 100% | Learning + anonymization |
| Audit | 0% | 100% | GDPR audit trail |
| Self-Improve | 0% | 100% | Usage patterns + suggestions |
| VDR | 0% | 100% | Permissions, watermarks, NDA, fence view |
| Gateway | 0% | 100% | Route proxy, auth middleware |

### 10.2 Migration Strategy: Monolith → Microservices

**Approach:** Strangler Fig pattern — extract services one at a time while keeping the monolith running.

**Phase 0 — Foundation (Do First):**
1. Add Redis to docker-compose
2. Create `shared/` library with event bus, DB helpers, auth middleware
3. Create API Gateway skeleton
4. Set up database schemas (init-schemas.sql)
5. Set up Alembic per-service

**Phase 1 — Extract Existing Services:**
1. Auth Service (no dependencies — extract first)
2. Project Service (depends on Auth)
3. DMS Service (depends on Auth + Project) — fix gaps during extraction
4. OCR Service (depends on DMS)
5. Agent Service (depends on all above) — LangGraph rewrite during extraction

**Phase 2 — Build New Services:**
6. Audit Service (universal event subscriber — build early)
7. Planning Service (the USP — high priority)
8. Report Service (key deliverable)
9. Finance Service
10. Knowledge Service
11. Self-Improvement Service (lowest priority)

---

## 11. Development Phases

Aligned with the Consolidated Development Plan (§18):

| Phase | Name | Services Involved | Key Deliverables |
|-------|------|-------------------|-----------------|
| 1 | Foundation | Gateway, Auth, Project | Microservice infrastructure, auth, projects, base frontend |
| 2 | Document Management | DMS, OCR | Upload, versioning, tagging, full-text search, OCR pipeline, VDR basics |
| 3 | AI Agents | Agent (LangGraph) | Orchestrator, 4 agents with parallel execution, cross-communication, confidence scoring |
| 4 | Financial Analysis | Finance | Data import, account mapping, variance analysis, benchmark comparison |
| 5 | Reporting | Report, Planning | Word/Excel reports, 5-phase audit planning, request list |
| 6 | Learning System | Knowledge, Self-Improve, Audit | Per-project learning, cross-project KB, GDPR audit trail, self-optimization |

---

## Appendix A: Technology Versions

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12+ | Backend services |
| FastAPI | 0.115+ | API framework |
| SQLAlchemy | 2.0+ | ORM (async) |
| PostgreSQL | 16 | Database |
| pgvector | 0.3+ | Vector embeddings |
| Redis | 7+ | Pub/sub + cache |
| LangGraph | latest | Agent orchestration |
| Vertex AI (Gemini) | 1.5-pro | LLM |
| text-embedding-004 | — | Embeddings (768-dim) |
| React | 19+ | Frontend |
| TypeScript | 5.9+ | Frontend language |
| Vite | 8+ | Build tool |
| Tailwind CSS | 3.4+ | Styling |
| Docker | latest | Containerization |
| Node.js | 22+ | Frontend runtime |

---

*AI DD v2.0 | March 2026 | CONFIDENTIAL*
