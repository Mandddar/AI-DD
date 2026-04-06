"""
Audit middleware — automatically logs every API request to the audit trail.
Attached as FastAPI middleware in main.py.
"""
import logging
from uuid import UUID
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from core.database import AsyncSessionLocal
from .models import AuditLog, AuditAction

logger = logging.getLogger(__name__)

# Paths that should not be logged (health checks, static, docs)
SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


def _extract_user_from_token(request: Request) -> tuple[str | None, str | None]:
    """Extract user_id and role from JWT token in Authorization header, without raising."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return None, None
    token = auth[7:]
    try:
        from core.security import decode_token
        payload = decode_token(token)
        user_id = payload.get("sub")
        return user_id, payload.get("role")
    except Exception:
        return None, None


async def _resolve_user_email(user_id: str, db) -> str | None:
    """Look up user email from database given a user_id string."""
    try:
        from modules.auth.models import User
        user = await db.get(User, user_id)
        return user.email if user else None
    except Exception:
        return None


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
        user_id_str, _ = _extract_user_from_token(request)

        async with AsyncSessionLocal() as db:
            user_email = None
            if user_id_str:
                user_email = await _resolve_user_email(user_id_str, db)

            log = AuditLog(
                user_id=user_id_str if user_id_str else None,
                user_email=user_email,
                action=AuditAction.data_accessed,
                resource_type="api",
                description=f"{request.method} {request.url.path} -> {status_code}",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")[:500],
            )
            db.add(log)
            await db.commit()
