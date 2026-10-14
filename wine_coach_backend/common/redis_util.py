"""
Redis 连接工具
基于 redis-py 封装，单例连接池（同步 + 异步各一个）
"""
import redis
import redis.asyncio as aioredis
import os

_redis_client: redis.Redis | None = None
_async_redis_client: aioredis.Redis | None = None


def get_redis() -> redis.Redis:
    """获取同步 Redis 客户端（单例）"""
    global _redis_client
    if _redis_client is None:
        password = os.getenv("REDIS_PASSWORD", "")
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=password if password else None,
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
        )
    return _redis_client


def get_async_redis() -> aioredis.Redis:
    """获取异步 Redis 客户端（单例，redis.asyncio）"""
    global _async_redis_client
    if _async_redis_client is None:
        password = os.getenv("REDIS_PASSWORD", "")
        _async_redis_client = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=password if password else None,
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
        )
    return _async_redis_client
