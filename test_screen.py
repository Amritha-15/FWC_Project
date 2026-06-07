import asyncio
from backend.database import session
from backend.services.ai_service import screen_job
from sqlalchemy import select
from backend.models.models import Job

async def main():
    session.init_db()
    async with session.async_session_maker() as db_session:
        result = await db_session.execute(
            select(Job.id).where(Job.status == 'Open')
        )
        job_ids = [row[0] for row in result.fetchall()]
        print("Open Jobs:", job_ids)

        for job_id in job_ids:
            print(f"Screening job {job_id}...")
            try:
                res = await screen_job(db_session, job_id)
                print(f"Result for job {job_id}:", res)
            except Exception as e:
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
