from backend.utils.cache import cached

# Re-export the existing Redis cache decorator for analytics modules

__all__ = ['cached']
