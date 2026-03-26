from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse, DisclaimerAcceptRequest
from .service import register_user, login_user, refresh_tokens
from .dependencies import current_user
from .models import User

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
