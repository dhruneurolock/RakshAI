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

async def start_redis_listener():
    """Start listening to Redis pubsub and broadcast to websockets."""
    from app.core.websocket_manager import websocket_manager
    import json
    import logging
    import asyncio
    
    logger = logging.getLogger(__name__)
    
    client = await get_redis()
    if not client:
        logger.warning("Could not start redis listener: No client available")
        return
        
    pubsub = client.pubsub()
    await pubsub.psubscribe("scan:*:progress")
    logger.info("Subscribed to Redis pattern: scan:*:progress")
    
    async def listener_loop():
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "pmessage":
                    data = message["data"]
                    try:
                        parsed = json.loads(data)
                        await websocket_manager.broadcast(parsed)
                    except Exception as e:
                        logger.error(f"Error broadcasting message: {e}")
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener loop died: {e}")
        finally:
            # Handle close carefully to prevent GeneratorExit errors
            try:
                await pubsub.close()
            except Exception:
                pass
            try:
                await client.aclose() if hasattr(client, "aclose") else await client.close()
            except Exception:
                pass
            
    task = asyncio.create_task(listener_loop())
    _listener_tasks = getattr(start_redis_listener, "tasks", set())
    _listener_tasks.add(task)
    task.add_done_callback(_listener_tasks.discard)
    start_redis_listener.tasks = _listener_tasks
