import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/Hrms_resume')
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with async_session() as session:
        res = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'leave_requests';"))
        for col in res.fetchall():
            print(col)

asyncio.run(main())
