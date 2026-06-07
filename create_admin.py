import asyncio
from backend.core.config import settings
from backend.core.security import get_password_hash
import asyncpg

EMAIL = 'admin@example.com'
PASSWORD = 'Password123'

async def main():
    conn = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        existing = await conn.fetchrow('SELECT id FROM users WHERE email=$1', EMAIL)
        if existing:
            print(f"Admin user already exists (id={existing['id']})")
            return
        pw = get_password_hash(PASSWORD)
        row = await conn.fetchrow('INSERT INTO users (name, email, password_hash, role) VALUES ($1,$2,$3,$4) RETURNING id', 'Admin', EMAIL, pw, 'admin')
        print(f"Created admin user id={row['id']} with email={EMAIL}")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
