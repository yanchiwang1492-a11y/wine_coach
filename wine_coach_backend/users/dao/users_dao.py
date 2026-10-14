"""
用户数据访问层
"""
from common.mysql_util import execute_query, execute_update


def query_user_by_name(user_name: str) -> dict | None:
    """按用户名查询用户（含密码哈希、邮箱、角色）"""
    sql = "SELECT user_id, user_name, password_hash, email, role_name FROM `user` WHERE user_name = %s"
    rows = execute_query(sql, (user_name,))
    return rows[0] if rows else None


def insert_user(user_name: str, password_hash: str, email: str | None = None, role_name: str = "user") -> int:
    """新增用户，返回 user_id"""
    sql = "INSERT INTO `user` (user_name, password_hash, email, role_name) VALUES (%s, %s, %s, %s)"
    return execute_update(sql, (user_name, password_hash, email, role_name))
