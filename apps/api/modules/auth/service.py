import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from fastapi import HTTPException, status
from .models import User, UserRole, TokenBlacklist, PasswordResetToken
from .schemas import RegisterRequest, LoginRequest, ChangePasswordRequest
from core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

logger = logging.getLogger(__name__)


# ── Registration & Login ───────────────────────────────────

async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.buyer,
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

    # If 2FA is enabled, verify TOTP code
    if user.totp_enabled:
        if not data.totp_code:
            # Signal that 2FA is required
            return {
                "access_token": "",
                "refresh_token": "",
                "token_type": "bearer",
                "requires_2fa": True,
            }
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(data.totp_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    payload = {"sub": str(user.id), "role": user.role.value}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
        "requires_2fa": False,
    }


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    # Check blacklist
    jti = payload.get("jti")
    if jti:
        bl = await db.scalar(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
        if bl:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Blacklist the old refresh token
    if jti:
        exp = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)
        db.add(TokenBlacklist(jti=jti, user_id=user.id, expires_at=exp))
        await db.commit()

    token_payload = {"sub": str(user.id), "role": user.role.value}
    return {
        "access_token": create_access_token(token_payload),
        "refresh_token": create_refresh_token(token_payload),
        "token_type": "bearer",
        "requires_2fa": False,
    }


async def get_current_user(db: AsyncSession, token: str) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    # Check token blacklist
    jti = payload.get("jti")
    if jti:
        bl = await db.scalar(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
        if bl:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ── Token Blacklist ────────────────────────────────────────

async def blacklist_token(db: AsyncSession, token: str, user_id: UUID) -> None:
    """Add a token to the blacklist (used on logout)."""
    payload = decode_token(token)
    jti = payload.get("jti")
    if not jti:
        return
    exp = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)
    existing = await db.scalar(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
    if not existing:
        db.add(TokenBlacklist(jti=jti, user_id=user_id, expires_at=exp))
        await db.commit()


async def cleanup_expired_blacklist(db: AsyncSession) -> int:
    """Remove expired blacklist entries to keep the table small."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        sql_delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
    )
    await db.commit()
    return result.rowcount


# ── 2FA / TOTP ─────────────────────────────────────────────

async def setup_totp(db: AsyncSession, user: User) -> dict:
    """Generate a new TOTP secret for the user (not yet enabled)."""
    secret = pyotp.random_base32()
    user.totp_secret = secret
    await db.commit()
    await db.refresh(user)

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="AI DD")
    return {"secret": secret, "provisioning_uri": uri}


async def verify_and_enable_totp(db: AsyncSession, user: User, code: str) -> bool:
    """Verify a TOTP code and enable 2FA if correct."""
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="Run 2FA setup first")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.totp_enabled = True
    await db.commit()
    await db.refresh(user)
    return True


async def disable_totp(db: AsyncSession, user: User, password: str) -> None:
    """Disable 2FA after verifying password."""
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    user.totp_secret = None
    user.totp_enabled = False
    await db.commit()
    await db.refresh(user)


# ── Password Change ────────────────────────────────────────

async def change_password(db: AsyncSession, user: User, data: ChangePasswordRequest) -> None:
    """Change password for an authenticated user."""
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()


# ── Password Reset ─────────────────────────────────────────

async def request_password_reset(db: AsyncSession, email: str) -> dict:
    """Generate a password reset token. Returns token in dev mode."""
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        # Don't reveal whether email exists — return success either way
        return {"message": "If this email is registered, a reset link has been sent."}

    # Invalidate any existing unused tokens
    existing = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id)
        .where(PasswordResetToken.used == False)
    )
    for tok in existing.scalars().all():
        tok.used = True

    reset_token = PasswordResetToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)
    await db.commit()
    await db.refresh(reset_token)

    # In production, send email here. In dev, return token directly.
    from core.config import get_settings
    settings = get_settings()
    result = {"message": "If this email is registered, a reset link has been sent."}
    if settings.is_dev:
        result["reset_token"] = reset_token.token
    return result


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> None:
    """Validate reset token and set new password."""
    reset_token = await db.scalar(
        select(PasswordResetToken)
        .where(PasswordResetToken.token == token)
        .where(PasswordResetToken.used == False)
    )
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if reset_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user = await db.get(User, reset_token.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(new_password)
    reset_token.used = True
    await db.commit()


# ── GDPR Account Deletion ─────────────────────────────────

async def delete_user_account(db: AsyncSession, user: User, password: str) -> None:
    """
    GDPR Article 17 — Right to deletion.
    Anonymizes or deletes all user data across tables.
    """
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    user_id = user.id

    # Log GDPR deletion request in audit trail (before deletion)
    from modules.audit.models import AuditLog, AuditAction
    db.add(AuditLog(
        user_id=user_id,
        user_email=user.email,
        action=AuditAction.gdpr_deletion_requested,
        resource_type="user",
        resource_id=str(user_id),
        description=f"GDPR deletion requested for user {user.email}",
    ))

    # Delete user's tokens
    await db.execute(sql_delete(TokenBlacklist).where(TokenBlacklist.user_id == user_id))
    await db.execute(sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id))

    # Delete project memberships
    from modules.projects.models import ProjectMember
    await db.execute(sql_delete(ProjectMember).where(ProjectMember.user_id == user_id))

    # Anonymize the user record instead of hard-deleting (preserve audit trail integrity)
    user.email = f"deleted_{user_id}@anonymized.local"
    user.full_name = "Deleted User"
    user.hashed_password = "DELETED"
    user.is_active = False
    user.totp_secret = None
    user.totp_enabled = False
    user.disclaimer_accepted = False

    # Log completion
    db.add(AuditLog(
        user_id=user_id,
        user_email="anonymized",
        action=AuditAction.gdpr_deletion_completed,
        resource_type="user",
        resource_id=str(user_id),
        description="GDPR deletion completed — user data anonymized",
    ))

    await db.commit()


# ── Profile Settings ───────────────────────────────────────

async def update_profile(db: AsyncSession, user: User, full_name: str | None, email: str | None) -> User:
    """Update user profile fields."""
    if full_name is not None:
        user.full_name = full_name

    if email is not None and email != user.email:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = email

    await db.commit()
    await db.refresh(user)
    return user
