"""
L2 摘要记忆：PostgreSQL 存储会话摘要（类封装）
每个 session_id 一条记录，增量更新（追加新对话到摘要）
"""
from common.pg_util import execute_query, execute_update


class SummaryMemory:
    """摘要记忆：PostgreSQL session_summary 表，按 session_id 隔离"""

    def __init__(self, session_id: str):
        self.session_id = session_id

    async def save(self, user_id: int, summary: str) -> None:
        """保存或更新会话摘要（UPSERT：存在则更新，不存在则插入）"""
        await execute_update(
            """
            INSERT INTO session_summary (session_id, user_id, summary)
            VALUES (%s, %s, %s)
            ON CONFLICT (session_id, user_id)
            DO UPDATE SET summary = EXCLUDED.summary
            """,
            (self.session_id, str(user_id), summary),
        )

    async def load(self, user_id: int) -> str:
        """读取会话摘要，不存在返回空字符串"""
        rows = await execute_query(
            "SELECT summary FROM session_summary WHERE session_id = %s AND user_id = %s",
            (self.session_id, str(user_id)),
        )
        return rows[0]["summary"] if rows else ""
