import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Optional Upstash client; don't fail if not installed in the environment
try:
    from upstash_redis import Redis as UpstashRedis
except Exception:
    UpstashRedis = None

# Load env variables from root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))


class Settings(BaseSettings):
    PROJECT_NAME: str = "HRMS Admin Dashboard"
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/Hrms_resume",
    )
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "hrms_super_secret_key_12345")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days to match Node expiresIn '7d'

    # Redis configuration (Upstash)
    REDIS_URL: str = os.environ.get("REDIS_URL", "")
    REDIS_TOKEN: str = os.environ.get("REDIS_TOKEN", "")
    # Traditional Redis config (hosted Redis instances)
    REDIS_HOST: str | None = os.environ.get("REDIS_HOST")
    REDIS_PORT: int | None = int(os.environ.get("REDIS_PORT")) if os.environ.get("REDIS_PORT") else None
    REDIS_USERNAME: str | None = os.environ.get("REDIS_USERNAME")
    REDIS_PASSWORD: str | None = os.environ.get("REDIS_PASSWORD")

    # SMTP / Email settings
    SMTP_HOST: str | None = os.environ.get("SMTP_HOST")
    SMTP_PORT: int | None = int(os.environ.get("SMTP_PORT")) if os.environ.get("SMTP_PORT") else None
    SMTP_USER: str | None = os.environ.get("SMTP_USER")
    SMTP_PASS: str | None = os.environ.get("SMTP_PASS")
    SMTP_FROM: str | None = os.environ.get("SMTP_FROM")

    class Config:
        case_sensitive = True


settings = Settings()

# Create Redis client if configuration is provided and client library available
redis = None
if settings.REDIS_URL and settings.REDIS_TOKEN and UpstashRedis is not None:
    redis = UpstashRedis(url=settings.REDIS_URL, token=settings.REDIS_TOKEN)
