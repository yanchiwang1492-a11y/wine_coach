"""
用户接口：注册 / 登录 / 登出 / 当前用户信息（JWT 认证）
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from users.entity.users_entity import RegisterRequest, LoginRequest
from users.service.users_service import register_user, login_user, logout_user
from common.jwt_decode import oauth2_scheme, get_current_user

users_router = APIRouter()


# ========== 注册 ==========
@users_router.post("/register", summary="注册")
async def register(req: RegisterRequest):
    """用户注册，注册成功自动登录，返回 JWT token"""
    token = register_user(req.user_name, req.password, req.email)
    return {"code": 200, "msg": "注册成功", "data": token}


# ========== 登录 ==========
@users_router.post("/login", summary="登录")
async def login(req: LoginRequest):
    """用户登录，返回 JWT token"""
    token = login_user(req.user_name, req.password)
    return {"code": 200, "msg": "登录成功", "data": token}


# ========== 登出 ==========
@users_router.post("/logout", summary="登出")
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    """用户登出：token 加入黑名单，立即失效"""
    logout_user(token)
    return {"code": 200, "msg": "退出登录成功", "data": None}


# ========== 当前用户信息 ==========
@users_router.get("/info", summary="当前用户信息")
async def user_info(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息（从 token 解出）"""
    return {"code": 200, "msg": "ok", "data": current_user}
