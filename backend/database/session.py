from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from backend.core.config import settings

# Lazily initialized engine and sessionmaker. Call init_db() during FastAPI startup.
DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker] = None

def init_db():
    """Initialize the async engine and sessionmaker. Call on app startup."""
    global engine, async_session_maker
    if engine is not None:
        return
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

async def close_db():
    """Dispose the engine on shutdown to close asyncpg connections."""
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None

async def get_async_db():
    if async_session_maker is None:
        raise RuntimeError("Async session maker not initialized. Call init_db() on app startup.")
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise