"""
L1 窗口记忆：Redis List 实现滑动窗口（类封装）
最近 N 条消息以 JSON 序列化存入 List，超出裁剪，过期时间刷新。
用 JSON 而非 "role:content" 字符串，避免 content 含冒号被误切。
"""
import json

from common.redis_util import get_async_redis

WINDOW_PREFIX = "window:"
WINDOW_SIZE = 20          # 窗口大小（N 条消息）
WINDOW_TTL = 86400        # 1 天过期（秒）


class WindowMemory:
    """窗口记忆：Redis List + JSON 序列化，按 session_id 隔离"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.key = WINDOW_PREFIX + session_id
        self._redis = get_async_redis()

    async def save(self, role: str, content: str) -> None:
        """写入一条消息（redis.asyncio 原生异步，不阻塞事件循环）"""
        msg = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        await self._redis.rpush(self.key, msg)
        await self._redis.ltrim(self.key, -WINDOW_SIZE, -1)
        await self._redis.expire(self.key, WINDOW_TTL)

    async def load(self) -> list[dict[str, str]]:
        """读取窗口内所有消息"""
        raw = await self._redis.lrange(self.key, 0, -1)
        return [json.loads(item) for item in raw]

    async def clear(self) -> None:
        """清空窗口"""
        await self._redis.delete(self.key)
