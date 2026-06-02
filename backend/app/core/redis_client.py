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


_redis_clients: dict = {}


async def get_redis() -> Optional[Any]:
    """
    Get or create Redis client instance per event loop
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return None
        
    # Completely fresh instance every time to avoid cross-loop/memory-address bugs
    client = aioredis.Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        single_connection_client=True
    )
    
    return client


async def close_redis():
    """Close Redis connection"""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        client = _redis_clients.pop(loop, None)
        if client:
            await client.close()
    except RuntimeError:
        pass
