from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse, DisclaimerAcceptRequest
from .service import register_user, login_user, refresh_tokens
from .dependencies import current_user, require_admin
from .models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


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


# ── Admin-only user management ──────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List all users. Admin only."""
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
    """Update a user's role. Admin only."""
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
    """Enable or disable a user account. Admin only."""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if str(target.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    target.is_active = data.is_active
    await db.commit()
    await db.refresh(target)
    return target
