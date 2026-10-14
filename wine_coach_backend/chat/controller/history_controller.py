"""
历史记录接口：会话列表/详情/新建/删除/重命名（对齐 wine_max，均需登录）
"""
from fastapi import APIRouter, Depends, Query
from common.jwt_decode import get_current_user
from chat.service.history_service import (
    list_sessions,
    get_session_detail,
    new_session,
    remove_session,
    rename_session,
)

history_router = APIRouter()


@history_router.get("/")
async def history_list(
    keyword: str = Query(None, description="搜索关键词"),
    current_user: dict = Depends(get_current_user),
):
    """获取用户的会话列表，支持关键词搜索"""
    user_id = current_user["user_id"]
    sessions = list_sessions(user_id, keyword)
    return {"code": 200, "msg": "ok", "data": sessions}


@history_router.get("/{session_id}")
async def history_detail(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取指定会话的消息列表"""
    user_id = current_user["user_id"]
    data = get_session_detail(session_id, user_id)
    return {"code": 200, "msg": "ok", "data": data}


@history_router.post("/new")
async def create_new_session(current_user: dict = Depends(get_current_user)):
    """新建一个空会话"""
    user_id = current_user["user_id"]
    data = new_session(user_id)
    return {"code": 200, "msg": "ok", "data": data}


@history_router.delete("/{session_id}")
async def delete_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除指定会话"""
    user_id = current_user["user_id"]
    ok = remove_session(session_id, user_id)
    if ok:
        return {"code": 200, "msg": "删除成功"}
    return {"code": 404, "msg": "会话不存在"}


@history_router.patch("/{session_id}")
async def rename_history(
    session_id: str,
    title: str = Query(..., description="新标题"),
    current_user: dict = Depends(get_current_user),
):
    """重命名会话"""
    user_id = current_user["user_id"]
    ok = rename_session(session_id, user_id, title)
    if ok:
        return {"code": 200, "msg": "重命名成功"}
    return {"code": 404, "msg": "会话不存在"}
