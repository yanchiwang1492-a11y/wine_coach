"""
JWT 工具：token 的生成与验证。
签名 = HMAC-SHA256(header.payload, SECRET_KEY)，验签用同一把密钥比对签名是否一致。
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
import os


def create_access_token(data: dict) -> str:
    """
    生成 JWT token（登录/注册成功后调用）

    Args:
        data: 要写入 token 的用户信息，如 {"user_id": 1, "user_name": "张三", "role_name": "user"}

    Returns:
        签好名的 token 字符串
    """
    copy_data = data.copy()  # 拷贝，避免修改调用方传入的字典

    # exp：过期时间；iat：签发时间（都用 UTC，避免时区差异）
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    copy_data.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    })

    # 用 SECRET_KEY 和 HS256 算法签名
    return jwt.encode(
        claims=copy_data,
        key=os.getenv("SECRET_KEY"),
        algorithm=os.getenv("ALGORITHM"),
    )


def verify_token(token: str) -> dict:
    """
    验证 token 有效性（受保护接口每次调用）

    Args:
        token: 前端传来的 token 字符串

    Returns:
        解密后的 payload（含 user_id / user_name / role_name 等）

    Raises:
        HTTPException(401): token 已过期或签名错误
    """
    try:
        payload = jwt.decode(
            token,
            key=os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401 未授权
            detail="token已过期或错误",
        )
