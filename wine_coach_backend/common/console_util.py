"""
Windows 控制台编码工具
"""
import sys


def ensure_utf8_console() -> None:
    """Windows 控制台默认 GBK，打印含非 ASCII 字符会编码崩溃，统一重配置为 UTF-8"""
    if sys.stdout.encoding and sys.stdout.encoding.lower() in ("gbk", "cp936"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
