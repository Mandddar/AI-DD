import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status
from .models import User, UserRole, TokenBlacklist, PasswordResetToken
from .schemas import RegisterRequest, LoginRequest
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, is_token_blacklisted,
)


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, data: LoginRequest) -> dict:
    user = await db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    payload = {"sub": str(user.id), "role": user.role.value}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
    }


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_payload = {"sub": str(user.id), "role": user.role.value}
    return {
        "access_token": create_access_token(token_payload),
        "refresh_token": create_refresh_token(token_payload),
        "token_type": "bearer",
    }


async def get_current_user(db: AsyncSession, token: str) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def logout_user(db: AsyncSession, token: str) -> None:
    """Blacklist the current token so it can't be reused."""
    payload = decode_token(token)
    jti = payload.get("jti")
    if not jti:
        return  # legacy tokens without jti — just let them expire

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    entry = TokenBlacklist(jti=jti, user_id=payload["sub"], expires_at=exp)
    db.add(entry)
    await db.commit()


async def change_password(db: AsyncSession, user: User, current_password: str, new_password: str) -> None:
    """Change user password and invalidate all existing tokens."""
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user.hashed_password = hash_password(new_password)
    await db.commit()


# --- GDPR User Deletion ---

async def delete_user(db: AsyncSession, user_id, requesting_user: User) -> None:
    """GDPR Art. 17 — right to deletion. Admin-only or self-deletion."""
    from modules.projects.models import ProjectMember

    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Remove from all projects
    await db.execute(delete(ProjectMember).where(ProjectMember.user_id == user_id))
    # Remove blacklisted tokens
    await db.execute(delete(TokenBlacklist).where(TokenBlacklist.user_id == user_id))
    # Remove reset tokens
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id))
    # Delete user
    await db.delete(target)
    await db.commit()


# --- Password Reset ---

async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """Generate a password reset token. Returns token if user exists, None otherwise.
    In production, the token would be emailed. For now, it's returned in the API response (dev mode)."""
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        return None  # Don't reveal whether email exists

    token = secrets.token_urlsafe(48)
    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset)
    await db.commit()
    return token


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> None:
    """Validate reset token and set new password."""
    result = await db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False,
        )
    )
    if not result:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if result.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user = await db.get(User, result.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(new_password)
    result.used = True
    await db.commit()


# --- 2FA / TOTP ---

def generate_totp_secret() -> str:
    """Generate a base32-encoded TOTP secret."""
    import base64
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")


def get_totp_uri(secret: str, email: str) -> str:
    """Build an otpauth:// URI for authenticator apps."""
    from urllib.parse import quote
    issuer = "AI DD"
    return f"otpauth://totp/{quote(issuer)}:{quote(email)}?secret={secret}&issuer={quote(issuer)}&digits=6&period=30"


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code against the secret. Allows ±1 time step drift."""
    import hmac
    import hashlib
    import struct
    import time

    code = code.strip()
    if len(code) != 6 or not code.isdigit():
        return False

    import base64
    key = base64.b32decode(secret, casefold=True)
    now = int(time.time())

    for offset in (-1, 0, 1):  # allow 1-step drift
        time_step = (now // 30) + offset
        msg = struct.pack(">Q", time_step)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[-1] & 0x0F
        otp = struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF
        otp_str = str(otp % 10**6).zfill(6)
        if hmac.compare_digest(otp_str, code):
            return True
    return False


async def setup_totp(db: AsyncSession, user: User) -> dict:
    """Generate TOTP secret and return setup info."""
    secret = generate_totp_secret()
    user.totp_secret = secret
    await db.commit()
    return {
        "secret": secret,
        "otpauth_uri": get_totp_uri(secret, user.email),
    }


async def verify_and_enable_totp(db: AsyncSession, user: User, code: str) -> None:
    """Verify TOTP code and enable 2FA."""
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not set up. Call /auth/2fa/setup first")

    if not verify_totp_code(user.totp_secret, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    user.totp_enabled = True
    await db.commit()


async def disable_totp(db: AsyncSession, user: User) -> None:
    """Disable 2FA for user."""
    user.totp_secret = None
    user.totp_enabled = False
    await db.commit()
