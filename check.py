import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/Hrms_resume')
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with async_session() as session:
        res = await session.execute(text('SELECT id, email, role, is_active FROM users;'))
        users = res.fetchall()
        for u in users:
            print(u)

asyncio.run(main())
