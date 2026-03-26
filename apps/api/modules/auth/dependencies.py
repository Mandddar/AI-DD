from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .models import User, UserRole
from .service import get_current_user

bearer = HTTPBearer()


async def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await get_current_user(db, credentials.credentials)


def require_role(*roles: UserRole):
    async def _check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _check


# Convenience shortcuts
require_admin = require_role(UserRole.admin)
require_advisor = require_role(UserRole.admin, UserRole.lead_advisor, UserRole.team_advisor)
