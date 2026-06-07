import os
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.models.models import User
from backend.core.security import verify_password, get_password_hash
from fastapi.testclient import TestClient
from backend.main import app

TARGET_PASSWORD = "Password123"

def get_sync_database_url():
    from backend.core.config import settings
    url = settings.DATABASE_URL
    # Normalize to psycopg driver for sync engine
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def check_and_fix_sync():
    sync_url = get_sync_database_url()
    engine = create_engine(sync_url)
    tested = []
    with Session(engine) as session:
        users = session.execute(select(User).filter(User.role == 'candidate')).scalars().all()
        for user in users:
            ok = verify_password(TARGET_PASSWORD, user.password_hash)
            entry = {"email": user.email, "id": user.id, "was_valid": ok}
            if not ok:
                new_hash = get_password_hash(TARGET_PASSWORD)
                user.password_hash = new_hash
                session.add(user)
                session.commit()
                entry["updated"] = True
            else:
                entry["updated"] = False
            tested.append(entry)

    # Test endpoints via TestClient (app startup will initialize async engine)
    results = []
    with TestClient(app) as client:
        for t in tested:
            email = t["email"]
            payload = {"email": email, "password": TARGET_PASSWORD}
            resp_cand = client.post("/api/candidate/login", json=payload)
            resp_auth = client.post("/api/auth/login", json=payload)
            results.append({
                "email": email,
                "was_valid_before": t["was_valid"],
                "updated": t["updated"],
                "candidate_login": {"status": resp_cand.status_code, "json": resp_cand.json()},
                "auth_login": {"status": resp_auth.status_code, "json": resp_auth.json()}
            })

    print("Tested accounts and results:")
    for r in results:
        print(r)

if __name__ == '__main__':
    check_and_fix_sync()
