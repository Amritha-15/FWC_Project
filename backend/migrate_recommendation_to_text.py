"""
One-shot migration script — run this directly with Python if you're not using Alembic.

Usage:
    python migrate_recommendation_to_text.py

Or if using Alembic, create a new revision and paste the upgrade/downgrade functions below.
"""

import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

async def run():
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Altering interview_results.recommendation → TEXT ...")
        await conn.execute("""
            ALTER TABLE interview_results
            ALTER COLUMN recommendation TYPE TEXT;
        """)
        print("✅ Done — recommendation is now TEXT")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())


# ── If you're using Alembic, paste this into a new revision file ──────────────
#
# def upgrade():
#     op.alter_column(
#         'interview_results', 'recommendation',
#         existing_type=sa.String(50),
#         type_=sa.Text(),
#         existing_nullable=True,
#     )
#
# def downgrade():
#     op.alter_column(
#         'interview_results', 'recommendation',
#         existing_type=sa.Text(),
#         type_=sa.String(50),
#         existing_nullable=True,
#     )