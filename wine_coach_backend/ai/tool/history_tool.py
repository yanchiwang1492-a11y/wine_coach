"""
历史记录工具：查询/保存会话消息
"""
from typing import Any
import uuid

from common.mysql_util import execute_query, execute_update, get_connection


def get_session_messages(session_id: str, user_id: int) -> list[dict[str, Any]]:
    """
    获取指定会话的所有消息（按时间升序）

    Returns:
        [{"role": "user"|"assistant", "content": "...", "created_at": "..."}]
    """
    sql = """
        SELECT role, content, created_at
        FROM practice_message
        WHERE session_id = %s AND user_id = %s
        ORDER BY created_at ASC
    """
    rows = execute_query(sql, (session_id, str(user_id)))
    return [
        {
            "role": r["role"],
            "content": r["content"],
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


def save_message(
    session_id: str,
    user_id: int,
    role: str,
    content: str,
) -> int:
    """
    保存一条消息到指定会话

    Returns:
        message_id
    """
    sql = """
        INSERT INTO practice_message (session_id, user_id, role, content, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    """
    return execute_update(sql, (session_id, user_id, role, content))


def update_session_title(session_id: str, user_id: int, title: str) -> int:
    """更新会话标题"""
    sql = """
        UPDATE practice_session
        SET title = %s, updated_at = NOW()
        WHERE session_id = %s AND user_id = %s
    """
    return execute_update(sql, (title, session_id, user_id))


def create_session(user_id: int, title: str = "新练习") -> str:
    """创建新会话，返回 session_id"""
    session_id = "sess_" + uuid.uuid4().hex[:12]
    sql = """
        INSERT INTO practice_session (session_id, user_id, title, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
    """
    execute_update(sql, (session_id, user_id, title))
    return session_id


def delete_session(session_id: str, user_id: int) -> bool:
    """删除会话及其所有消息（事务，避免孤儿消息）"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM practice_message WHERE session_id = %s AND user_id = %s",
            (session_id, str(user_id)),
        )
        cursor.execute(
            "DELETE FROM practice_session WHERE session_id = %s AND user_id = %s",
            (session_id, str(user_id)),
        )
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    except Exception:
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
