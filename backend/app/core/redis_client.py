"""
Redis Client Configuration
Provides async Redis connection for agents
"""
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None
from typing import Optional, Any
from app.core.config import settings


_redis_client: Optional[Any] = None


async def get_redis() -> Optional[Any]:
    """
    Get or create Redis client instance
    Returns singleton Redis connection
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10
        )
    
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
