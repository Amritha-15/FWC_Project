import functools
import json
import logging
from typing import Callable, Any
from redis import Redis
from backend.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RedisCache")

# Initialize Redis client connection
redis_client: Any = None

try:
    if settings.REDIS_HOST:
        # Build kwargs dynamically based on credentials
        redis_kwargs = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "decode_responses": True,
            "socket_timeout": 2.0
        }
        if settings.REDIS_USERNAME:
            redis_kwargs["username"] = settings.REDIS_USERNAME
        if settings.REDIS_PASSWORD:
            redis_kwargs["password"] = settings.REDIS_PASSWORD
            
        redis_client = Redis(**redis_kwargs)
        # Test connection ping
        redis_client.ping()
        logger.info(f"✅ Connected to Redis Cloud at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    else:
        logger.info("ℹ️ Redis HOST not configured. Caching is disabled.")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}. Falling back to direct database execution (caching bypassed).")
    redis_client = None


def cached(ttl_seconds: int = 300) -> Callable:
    """
    Decorator to cache endpoint returns in Redis.
    Uses function name and arguments as the cache key.
    Enforces TTL (default 5 mins) and logs hits/misses.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if redis_client is None:
                # Cache bypassed
                return await func(*args, **kwargs)

            # Construct unique cache key
            key_parts = [func.__name__]
            # Skip database session arguments when building the cache key
            for arg in args[1:]:  # skip 'self' or DB session
                if 'Session' not in str(type(arg)):
                    key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                if 'db' not in k:
                    key_parts.append(f"{k}:{v}")
            cache_key = ":".join(key_parts)

            try:
                # Check cache
                cached_val = redis_client.get(cache_key)
                if cached_val:
                    logger.info(f"🎯 CACHE HIT: key='{cache_key}'")
                    return json.loads(cached_val)
                
                logger.info(f"⚡ CACHE MISS: key='{cache_key}'")
                # Call underlying database/service function
                result = await func(*args, **kwargs)
                
                # Store in cache
                redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
                return result
            except Exception as ex:
                logger.warning(f"⚠️ Redis Cache Error (reading/writing): {ex}. Direct DB fallback used.")
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def clear_cache_pattern(pattern: str = "*"):
    """
    Utility to purge cache keys matching a specific pattern.
    Useful for clearing dashboard stats when actions like user creation / role changes occur!
    """
    if redis_client is None:
        return
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"🧹 Cleared {len(keys)} cached keys matching pattern: {pattern}")
    except Exception as ex:
        logger.warning(f"⚠️ Redis Cache Clear Error: {ex}")
