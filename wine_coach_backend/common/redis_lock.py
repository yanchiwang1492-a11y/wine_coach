"""
分布式会话锁：基于 Redis + Lua 脚本，保证同一 session 同时只有一个请求处理。
释放锁用 Lua 脚本把「校验 token + DEL」合成一步原子操作，避免误删别人的锁。
"""
from contextlib import asynccontextmanager
import uuid

from common.redis_util import get_async_redis

LOCK_PREFIX = "lock:session:"
# 锁过期时间（秒）：防止异常崩溃导致锁永久占用
DEFAULT_TTL = 300  # 5 分钟

# 释放锁的 Lua 脚本：只有锁的持有者（token 匹配）才能释放
_UNLOCK_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""

@asynccontextmanager
async def session_lock(session_id: str, ttl: int = DEFAULT_TTL):
    """
    会话锁异步上下文管理器（redis.asyncio 原生异步）

    使用方式：
        async with session_lock(session_id):
            # 要加锁的代码（跑图等）

    Raises:
        RuntimeError: 获取锁失败（会话正在处理中）
    """
    redis = get_async_redis()
    key = LOCK_PREFIX + session_id
    token = uuid.uuid4().hex  # 锁的持有者标识，防止误删别人的锁

    # SETNX(SET if Not eXists)：key 不存在才设置成功（获取锁）
    ok = await redis.set(key, token, nx=True, ex=ttl)
    if not ok:
        raise RuntimeError("会话忙，请稍后再试")
    try:
        yield
    finally:
        # 用 Lua 脚本原子释放锁
        try:
            await redis.eval(_UNLOCK_LUA, 1, key, token)
        except Exception:
            pass  # 释放失败不抛错，让它自己过期
