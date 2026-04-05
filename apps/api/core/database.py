from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_dev,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables on startup (dev only — use Alembic in prod)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_admin()


async def _seed_admin():
    """Ensure default admin users exist on startup."""
    from sqlalchemy import select
    from modules.auth.models import User, UserRole
    from core.security import hash_password

    users = [
        {
            "email": "ayush@gmail.com",
            "password": "ayush@19",
            "full_name": "ayush chandekar",
        },
        {
            "email": "aystar@gmail.com",
            "password": "aystar@19",
            "full_name": "aystar gaming",
        },
    ]

    async with AsyncSessionLocal() as db:
        for u in users:
            result = await db.execute(select(User).where(User.email == u["email"]))
            if result.scalar_one_or_none():
                continue  # don't return, just skip

            db.add(User(
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=UserRole.admin,
                is_active=True,
                disclaimer_accepted=True,
            ))

        await db.commit()