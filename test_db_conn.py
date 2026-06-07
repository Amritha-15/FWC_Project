import asyncio
from backend.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_db():
    url = settings.DATABASE_URL
    # normalize postgres URL to asyncpg driver like backend.session.py does
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    print("Using DATABASE_URL:", url)
    try:
        engine = create_async_engine(url, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar_one()
            print("DB SELECT 1 result:", val)
        await engine.dispose()
        print("DB connection successful")
    except Exception as e:
        print("DB connection failed:", e)

if __name__ == '__main__':
    asyncio.run(test_db())
