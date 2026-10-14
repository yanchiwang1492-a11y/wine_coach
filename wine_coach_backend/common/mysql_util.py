"""
MySQL 数据库连接工具
基于 pymysql + DBUtils 连接池（池化复用，避免每次请求新建连接）
"""
import os

import pymysql
from dbutils.pooled_db import PooledDB

# 全局连接池（懒初始化）
_pool: PooledDB | None = None


def _get_pool() -> PooledDB:
    """获取连接池（单例，首次调用时创建）"""
    global _pool
    if _pool is None:
        _pool = PooledDB(
            creator=pymysql,
            maxconnections=20,   # 最大连接数
            mincached=1,         # 启动时创建的空闲连接数
            maxcached=10,        # 空闲连接池最大缓存数
            blocking=True,       # 池满时阻塞等待空闲连接（而非直接报错）
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            db=os.getenv("DB_NAME", "wine_coach"),
            charset=os.getenv("DB_CHARSET", "utf8mb4"),
            cursorclass=pymysql.cursors.DictCursor,
        )
    return _pool


def get_connection() -> pymysql.Connection:
    """从池中获取一个连接（close 时会归还给池，不会真正断开）"""
    return _get_pool().connection()


def execute_query(sql: str, params: tuple | None = None) -> list[dict]:
    """
    执行查询 SQL，返回结果列表（字典形式）

    Args:
        sql: SQL 语句，用 %s 占位
        params: 参数元组

    Returns:
        查询结果列表
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_update(sql: str, params: tuple | None = None) -> int:
    """
    执行写入 SQL（INSERT/UPDATE/DELETE），返回受影响行数或自增ID

    Args:
        sql: SQL 语句
        params: 参数元组

    Returns:
        INSERT 返回自增 ID，其他返回受影响行数
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        if sql.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        return cursor.rowcount
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
