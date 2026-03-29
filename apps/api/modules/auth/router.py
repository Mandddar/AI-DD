from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.config import get_settings
from .schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserResponse, DisclaimerAcceptRequest,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    TOTPSetupResponse, TOTPVerifyRequest,
)
from .service import (
    register_user, login_user, refresh_tokens, logout_user, change_password,
    delete_user, request_password_reset, confirm_password_reset,
    setup_totp, verify_and_enable_totp, disable_totp, verify_totp_code,
)
from .dependencies import current_user, require_admin
from .models import User

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer()
settings = get_settings()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await register_user(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    tokens = await login_user(db, data)

    # If user has 2FA enabled, the frontend must call /auth/2fa/verify after login
    # For now, we include a flag in the response
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_tokens(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return user


@router.post("/disclaimer/accept", response_model=UserResponse)
async def accept_disclaimer(
    data: DisclaimerAcceptRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    user.disclaimer_accepted = data.accepted
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/logout", status_code=204)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    await logout_user(db, credentials.credentials)


@router.patch("/me/password", status_code=204)
async def update_password(
    data: PasswordChangeRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await change_password(db, user, data.current_password, data.new_password)


# --- GDPR User Deletion ---

@router.delete("/users/{user_id}", status_code=204)
async def gdpr_delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """GDPR Art. 17 — admin can delete any user."""
    await delete_user(db, user_id, user)


@router.delete("/me", status_code=204)
async def delete_own_account(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """GDPR Art. 17 — user can delete their own account."""
    await delete_user(db, user.id, user)


# --- Password Reset ---

@router.post("/password-reset/request", status_code=200)
async def password_reset_request(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset. In production, token is emailed. In dev, returned in response."""
    token = await request_password_reset(db, data.email)
    if settings.is_dev and token:
        return {"message": "Reset token generated", "token": token}
    # Always return success to avoid leaking whether email exists
    return {"message": "If this email is registered, a reset link has been sent"}


@router.post("/password-reset/confirm", status_code=204)
async def password_reset_confirm(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Confirm password reset with token."""
    await confirm_password_reset(db, data.token, data.new_password)


# --- 2FA / TOTP ---

@router.post("/2fa/setup", response_model=TOTPSetupResponse)
async def totp_setup(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate TOTP secret. User must verify with /2fa/verify to activate."""
    return await setup_totp(db, user)


@router.post("/2fa/verify", status_code=200)
async def totp_verify(
    data: TOTPVerifyRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify TOTP code to enable 2FA."""
    await verify_and_enable_totp(db, user, data.code)
    return {"message": "2FA enabled successfully"}


@router.delete("/2fa", status_code=204)
async def totp_disable(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA for current user."""
    await disable_totp(db, user)
