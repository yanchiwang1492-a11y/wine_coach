"""
PostgreSQL 连接工具
基于 psycopg v3 + AsyncConnectionPool（异步连接池）
供 L2 摘要记忆（session_summary 表）与 LangGraph checkpointer 共用同一个池
"""
import os

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

# 全局连接池（启动时由 AppContext 初始化并 open）
_pool: AsyncConnectionPool | None = None


def init_pool(conninfo: str) -> AsyncConnectionPool:
    """初始化连接池（open=False，需调用 open_pool 激活）"""
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=conninfo,
            max_size=20,     # 最大连接数
            min_size=1,      # 最小连接数
            open=False,      # 手动 open（在 lifespan 里 await open_pool）
            timeout=5,       # 从池取连接的等待超时（秒）
            kwargs={"row_factory": dict_row},  # 连接默认返回字典行
        )
    return _pool


async def open_pool() -> None:
    """激活连接池（在应用启动时调用）"""
    if _pool is not None:
        await _pool.open()

async def execute_query(sql: str, params: tuple | None = None) -> list[dict]:
    """执行查询 SQL，返回字典列表"""
    async with _pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or ())
            return await cur.fetchall()


async def execute_update(sql: str, params: tuple | None = None) -> int:
    """执行写入 SQL，返回受影响行数"""
    async with _pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or ())
            await conn.commit()
            return cur.rowcount
