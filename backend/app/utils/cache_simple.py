# backend/app/utils/cache_simple.py
# Redis disabled for now — simple no-op cache

def cache_get(key: str):
    return None

def cache_set(key: str, value: dict, ttl: int = 86400):
    # no-op
    return None
