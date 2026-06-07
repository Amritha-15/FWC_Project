import asyncio
import asyncpg
from backend.core.config import settings
from backend.core.security import get_password_hash, verify_password

TARGET_PW = "Password123"

async def run():
    conn = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        new_hash = get_password_hash(TARGET_PW)
        updated = []

        # Update one user per role: admin, hr, manager
        for role in ('admin', 'hr', 'manager'):
            row = await conn.fetchrow('SELECT id, name, email, role FROM users WHERE role=$1 ORDER BY id LIMIT 1', role)
            if row:
                await conn.execute('UPDATE users SET password_hash=$1 WHERE id=$2', new_hash, row['id'])
                updated.append({'id': row['id'], 'email': row['email'], 'name': row['name'], 'role': row['role']})

        # Update a user named Sam (case-insensitive prefix match)
        sam = await conn.fetchrow("SELECT id, name, email, role FROM users WHERE lower(name) LIKE 'sam%' ORDER BY id LIMIT 1")
        if sam:
            await conn.execute('UPDATE users SET password_hash=$1 WHERE id=$2', new_hash, sam['id'])
            updated.append({'id': sam['id'], 'email': sam['email'], 'name': sam['name'], 'role': sam['role']})

        print('Updated users:', updated)

        # Verify password for those users
        for u in updated:
            row = await conn.fetchrow('SELECT password_hash FROM users WHERE id=$1', u['id'])
            ok = verify_password(TARGET_PW, row['password_hash'])
            print(f"id={u['id']} email={u['email']} matches={ok}")

    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(run())
