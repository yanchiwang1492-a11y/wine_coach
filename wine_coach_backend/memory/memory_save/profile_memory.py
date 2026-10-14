"""
L4 用户画像：Redis Hash 存储（类封装）
按 user_id 隔离，永久不过期。
"""
from common.redis_util import get_async_redis

KEY_PREFIX = "profile:"

# 画像字段 → 中文标签（供回显与 prompt 组装使用）
FIELD_LABELS = {
    "company_type": "公司类型",
    "sales_channel": "销售渠道",
    "product_focus": "主营国家",
    "customer_group": "主要客户",
    "goal": "提升目标",
}


class ProfileMemory:
    """用户画像：Redis Hash，按 user_id 隔离"""

    _FIELDS = tuple(FIELD_LABELS.keys())

    def __init__(self, user_id: int | str):
        self.user_id = str(user_id)
        self.key = KEY_PREFIX + self.user_id
        self._redis = get_async_redis()

    async def load(self) -> dict:
        """读取用户画像，缺失字段自动补空串"""
        data = await self._redis.hgetall(self.key)
        return {k: data.get(k, "") for k in self._FIELDS}

    async def update(self, updates: dict) -> None:
        """批量更新画像字段（仅写入非空且合法的字段，保留其余旧值）"""
        mapping = {k: str(v) for k, v in updates.items() if v and k in self._FIELDS}
        if mapping:
            await self._redis.hset(self.key, mapping=mapping)

    async def is_empty(self) -> bool:
        """画像是否为空（判断是否需要首次采集）"""
        return not any((await self.load()).values())
