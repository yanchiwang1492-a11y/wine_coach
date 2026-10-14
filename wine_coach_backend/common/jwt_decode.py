"""
认证依赖：OAuth2PasswordBearer 从 Authorization: Bearer <token> 头解析 token，
get_current_user 完成「验签 + 查黑名单」，接口用 Depends(get_current_user) 注入即可。
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from common.jwt_util import verify_token
from common.token_blacklist import is_blacklisted

# 从 Authorization: Bearer <token> 头里解析 token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    获取当前登录用户（作为依赖注入到受保护接口）

    两步校验：
    1. verify_token：验签 + 过期时间
    2. is_blacklisted：是否已退出登录（黑名单）
    """
    payload = verify_token(token)  # 第一步：验证签名与过期时间
    if is_blacklisted(token):      # 第二步：检查是否已退出登录（黑名单）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token已失效，请重新登录",
        )
    return payload


def verify_token_or_none(token: str) -> dict | None:
    """
    验证 token，返回 payload；无效或已拉黑返回 None（不抛异常）

    供 WebSocket 等无法走 Depends 依赖注入的场景手动鉴权使用。
    """
    try:
        payload = verify_token(token)
    except HTTPException:
        return None
    if is_blacklisted(token):
        return None
    return payload
