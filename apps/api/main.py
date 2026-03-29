from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db
from core.config import get_settings
from modules.auth.router import router as auth_router
from modules.projects.router import router as projects_router
from modules.dms.router import router as dms_router
from modules.agent.router import router as agent_router
from modules.planning.router import router as planning_router
from modules.finance.router import router as finance_router
from modules.report.router import router as report_router
from modules.knowledge.router import router as knowledge_router
from modules.audit.router import router as audit_router
from modules.self_improvement.router import router as self_improvement_router
from modules.audit.middleware import AuditMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI DD API",
    description="AI-powered M&A Due Diligence Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit trail middleware — logs every API request
app.add_middleware(AuditMiddleware)

# ── Module Routers ──────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(dms_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(planning_router, prefix="/api/v1")
app.include_router(finance_router, prefix="/api/v1")
app.include_router(report_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(self_improvement_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-dd-api"}
