import asyncio
from backend.database import session
from sqlalchemy import text

async def main():
    session.init_db()
    async with session.async_session_maker() as db:
        res = await db.execute(text("SELECT id, hiring_recommendation FROM applications"))
        for row in res.fetchall():
            print(f"ID: {row[0]}, Recommendation: {repr(row[1])}")

if __name__ == "__main__":
    asyncio.run(main())
