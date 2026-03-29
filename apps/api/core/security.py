from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict[str, Any]) -> str:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {**data, "exp": expire, "type": "access", "jti": jti},
        settings.secret_key, algorithm=settings.algorithm,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {**data, "exp": expire, "type": "refresh", "jti": jti},
        settings.secret_key, algorithm=settings.algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def is_token_blacklisted(jti: str, db: AsyncSession) -> bool:
    from modules.auth.models import TokenBlacklist
    result = await db.scalar(
        select(TokenBlacklist.id).where(TokenBlacklist.jti == jti).limit(1)
    )
    return result is not None
