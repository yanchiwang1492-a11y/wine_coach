"""
密码工具：bcrypt 哈希与校验
直接用 bcrypt 库（避免 passlib 1.7.4 与 bcrypt 4.x 的兼容性问题）
"""
import bcrypt


def hash_password(password: str) -> str:
    """明文密码 → bcrypt 哈希（返回字符串）"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False
