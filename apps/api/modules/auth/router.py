from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .schemas import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse,
    DisclaimerAcceptRequest, TotpSetupResponse, TotpVerifyRequest, TotpDisableRequest,
    ChangePasswordRequest, PasswordResetRequestSchema, PasswordResetConfirmSchema,
    AccountDeleteRequest, UpdateProfileRequest,
)
from .service import (
    register_user, login_user, refresh_tokens,
    setup_totp, verify_and_enable_totp, disable_totp,
    change_password, request_password_reset, confirm_password_reset,
    delete_user_account, update_profile, blacklist_token,
)
from .dependencies import current_user, require_admin
from .models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Registration & Login ───────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await register_user(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_user(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_tokens(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return user


@router.post("/logout")
async def logout(
    request: Request,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout — blacklists the current access token."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    if token:
        await blacklist_token(db, token, user.id)
    return {"message": "Logged out successfully"}


# ── Disclaimer ─────────────────────────────────────────────

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


# ── 2FA / TOTP ─────────────────────────────────────────────

@router.post("/2fa/setup", response_model=TotpSetupResponse)
async def totp_setup(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate TOTP secret and provisioning URI (QR code data).
    Per spec §5.3: 2FA enforced for external users, optional for internal, required for admin.
    """
    return await setup_totp(db, user)


@router.post("/2fa/verify", response_model=UserResponse)
async def totp_verify(
    data: TotpVerifyRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify TOTP code to enable 2FA."""
    await verify_and_enable_totp(db, user, data.code)
    return user


@router.post("/2fa/disable", response_model=UserResponse)
async def totp_disable(
    data: TotpDisableRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA (requires password confirmation)."""
    await disable_totp(db, user, data.password)
    return user


# ── Password Change ────────────────────────────────────────

@router.post("/change-password")
async def change_pwd(
    data: ChangePasswordRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the currently authenticated user."""
    await change_password(db, user, data)
    return {"message": "Password changed successfully"}


# ── Password Reset (unauthenticated) ──────────────────────

@router.post("/password-reset/request")
async def pwd_reset_request(
    data: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset token. In dev mode, returns the token directly."""
    return await request_password_reset(db, data.email)


@router.post("/password-reset/confirm")
async def pwd_reset_confirm(
    data: PasswordResetConfirmSchema,
    db: AsyncSession = Depends(get_db),
):
    """Confirm password reset with token and set new password."""
    await confirm_password_reset(db, data.token, data.new_password)
    return {"message": "Password has been reset successfully"}


# ── Settings / Profile ─────────────────────────────────────

@router.patch("/settings", response_model=UserResponse)
async def update_settings(
    data: UpdateProfileRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile (name, email)."""
    return await update_profile(db, user, data.full_name, data.email)


# ── GDPR Account Deletion ─────────────────────────────────

@router.post("/account/delete")
async def delete_account(
    data: AccountDeleteRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """GDPR Article 17 — permanently anonymize all user data."""
    if data.confirmation != "DELETE MY ACCOUNT":
        raise HTTPException(status_code=400, detail='Type "DELETE MY ACCOUNT" to confirm')
    await delete_user_account(db, user, data.password)
    return {"message": "Account has been permanently deleted per GDPR Article 17"}


# ── Admin-only user management ─────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


class UpdateRoleRequest(BaseModel):
    role: UserRole


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    data: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if str(target.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    target.role = data.role
    await db.commit()
    await db.refresh(target)
    return target


class ToggleActiveRequest(BaseModel):
    is_active: bool


@router.patch("/users/{user_id}/active", response_model=UserResponse)
async def toggle_user_active(
    user_id: str,
    data: ToggleActiveRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if str(target.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    target.is_active = data.is_active
    await db.commit()
    await db.refresh(target)
    return target


# ── Admin: GDPR delete any user ────────────────────────────

@router.delete("/users/{user_id}/gdpr", status_code=200)
async def admin_gdpr_delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin-triggered GDPR deletion of any user account."""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if str(target.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot delete your own account via admin endpoint")

    # Use a dummy password check bypass for admin-triggered deletion
    from modules.audit.models import AuditLog, AuditAction
    from sqlalchemy import delete as sql_delete
    from .models import TokenBlacklist, PasswordResetToken
    from modules.projects.models import ProjectMember

    db.add(AuditLog(
        user_id=admin.id,
        user_email=admin.email,
        action=AuditAction.gdpr_deletion_requested,
        resource_type="user",
        resource_id=str(target.id),
        description=f"Admin GDPR deletion for user {target.email}",
    ))

    await db.execute(sql_delete(TokenBlacklist).where(TokenBlacklist.user_id == target.id))
    await db.execute(sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == target.id))
    await db.execute(sql_delete(ProjectMember).where(ProjectMember.user_id == target.id))

    target.email = f"deleted_{target.id}@anonymized.local"
    target.full_name = "Deleted User"
    target.hashed_password = "DELETED"
    target.is_active = False
    target.totp_secret = None
    target.totp_enabled = False

    db.add(AuditLog(
        user_id=admin.id,
        user_email=admin.email,
        action=AuditAction.gdpr_deletion_completed,
        resource_type="user",
        resource_id=str(target.id),
        description="Admin GDPR deletion completed",
    ))

    await db.commit()
    return {"message": f"User {user_id} has been GDPR-deleted"}
