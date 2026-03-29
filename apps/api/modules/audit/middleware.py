"""
Audit middleware — automatically logs every API request to the audit trail.
Attached as FastAPI middleware in main.py.
"""
import logging
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from core.database import AsyncSessionLocal
from .models import AuditLog, AuditAction

logger = logging.getLogger(__name__)

# Paths that should not be logged (health checks, static, docs)
SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Skip non-essential paths
        if request.url.path in SKIP_PATHS:
            return response

        # Log the request asynchronously
        try:
            await self._log_request(request, response.status_code)
        except Exception as e:
            logger.warning("Audit logging failed: %s", e)

        return response

    async def _log_request(self, request: Request, status_code: int):
        async with AsyncSessionLocal() as db:
            log = AuditLog(
                action=AuditAction.data_accessed,
                resource_type="api",
                description=f"{request.method} {request.url.path} -> {status_code}",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")[:500],
            )
            db.add(log)
            await db.commit()
