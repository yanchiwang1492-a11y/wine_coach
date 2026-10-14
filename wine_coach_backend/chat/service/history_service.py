"""
历史记录服务层
"""
from typing import Any
from ai.tool.history_tool import (
    get_session_messages,
    update_session_title,
    create_session as create_session_tool,
    delete_session as delete_session_tool,
)
from common.mysql_util import execute_query


def list_sessions(user_id: int, keyword: str | None = None) -> list[dict[str, Any]]:
    """
    获取用户的会话列表

    搜索：LIKE %% 模糊匹配标题
    排序：按更新时间倒序
    """
    if keyword:
        sql = """
            SELECT session_id, title, updated_at
            FROM practice_session
            WHERE user_id = %s AND title LIKE %s
            ORDER BY updated_at DESC
        """
        rows = execute_query(sql, (str(user_id), f"%{keyword}%"))
    else:
        sql = """
            SELECT session_id, title, updated_at
            FROM practice_session
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """
        rows = execute_query(sql, (str(user_id),))

    return [
        {
            "session_id": r["session_id"],
            "title": r["title"] or "新练习",
            "updated_at": str(r["updated_at"]),
        }
        for r in rows
    ]


def get_session_detail(session_id: str, user_id: int) -> dict:
    """获取会话详情（标题 + 更新时间 + 消息列表）"""
    sql = "SELECT title, updated_at FROM practice_session WHERE session_id = %s AND user_id = %s"
    rows = execute_query(sql, (session_id, str(user_id)))
    title = rows[0]["title"] if rows else "新练习"
    updated_at = str(rows[0]["updated_at"]) if rows else ""

    return {
        "session_id": session_id,
        "title": title,
        "updated_at": updated_at,
        "messages": get_session_messages(session_id, user_id),
    }


def new_session(user_id: int) -> dict[str, Any]:
    """新建会话"""
    session_id = create_session_tool(user_id)
    return {"session_id": session_id, "title": "新练习"}


def remove_session(session_id: str, user_id: int) -> bool:
    """删除会话"""
    return delete_session_tool(session_id, user_id)


def rename_session(session_id: str, user_id: int, title: str) -> bool:
    """重命名会话"""
    count = update_session_title(session_id, user_id, title)
    return count > 0
