"""
用户相关 Pydantic Schema
"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求（email 选填，用于后续发送评估报告）"""
    user_name: str = Field(..., description="用户名", min_length=2, max_length=20)
    password: str = Field(..., description="密码", min_length=6, max_length=32)
    email: str | None = Field(None, description="邮箱（选填）")


class LoginRequest(BaseModel):
    """登录请求"""
    user_name: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
