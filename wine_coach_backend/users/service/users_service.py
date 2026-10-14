"""
用户业务逻辑层：注册 / 登录 / 登出（JWT）
"""
from fastapi import HTTPException

from users.dao.users_dao import query_user_by_name, insert_user
from common.password_util import hash_password, verify_password
from common.jwt_util import create_access_token
from common.token_blacklist import add_blacklist


def register_user(user_name: str, password: str, email: str | None = None) -> str:
    """
    注册用户，成功后直接返回 JWT token（注册即登录）

    Returns:
        JWT token 字符串
    """
    existing = query_user_by_name(user_name)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已被注册")

    password_hash = hash_password(password)
    user_id = insert_user(user_name, password_hash, email)

    # 注册成功直接生成 token 自动登录
    return create_access_token({
        "user_id": user_id,
        "user_name": user_name,
        "role_name": "user",
        "email": email,
    })


def login_user(user_name: str, password: str) -> str:
    """
    登录：验证密码后返回 JWT token

    Returns:
        JWT token 字符串
    """
    user = query_user_by_name(user_name)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    return create_access_token({
        "user_id": user["user_id"],
        "user_name": user["user_name"],
        "role_name": user["role_name"],
        "email": user["email"],
    })


def logout_user(token: str) -> None:
    """登出：把 token 加入黑名单，使其立即失效"""
    add_blacklist(token)
