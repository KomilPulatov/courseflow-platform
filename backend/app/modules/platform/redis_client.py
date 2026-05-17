from functools import lru_cache

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis | None:
    """Return one shared Redis client, or None when Redis is disabled."""

    if not settings.REDIS_ENABLED:
        return None
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
    )


def create_async_redis_client() -> AsyncRedis | None:
    """Async Redis is only needed by the WebSocket listener."""

    if not settings.REDIS_ENABLED:
        return None
    return AsyncRedis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
    )
