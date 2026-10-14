"""
token 黑名单：退出登录后让 token 立即失效。
JWT 无状态、签发后过期前一直有效，故退出时把 token 写入 Redis 黑名单（TTL=剩余有效期），
每次鉴权先查黑名单，命中则拒绝。
"""
import os
import time
import hashlib
from jose import JWTError, jwt

from common.redis_util import get_redis


def _key(token: str) -> str:
    """生成黑名单的 Redis key（token 太长，用 sha256 摘要作 key，避免超长）"""
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"blacklist:{digest}"


def add_blacklist(token: str) -> None:
    """把 token 加入黑名单，TTL 设为剩余有效时间"""
    try:
        # 解码拿 exp（过期时间戳，单位秒），不校验也能解出 claims
        payload = jwt.decode(
            token,
            key=os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )
    except JWTError:
        return  # token 本身非法，无需加入黑名单

    exp = payload.get("exp")
    remaining = int(exp - time.time()) if exp else 0  # 剩余有效秒数
    if remaining <= 0:
        return  # 已过期，无需黑名单

    redis = get_redis()
    redis.set(_key(token), "1", ex=remaining)  # 存黑名单，到期自动删除


def is_blacklisted(token: str) -> bool:
    """检查 token 是否已被拉黑"""
    return get_redis().exists(_key(token)) == 1
