"""
Chroma 向量数据库工具（用于 L3 长期记忆）
单例模式，启动时初始化
"""
from typing import Any
import chromadb
import os

_chroma_client: Any = None
_collection: Any = None


def get_client() -> Any:
    """获取 Chroma 客户端（单例）"""
    global _chroma_client
    if _chroma_client is None:
        persist_path = os.getenv("CHROMA_PATH")
        os.makedirs(persist_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_path)
    return _chroma_client


def get_collection() -> Any:
    """获取长期记忆 collection（单例）"""
    global _collection
    if _collection is None:
        client = get_client()
        collection_name = os.getenv("CHROMA_COLLECTION")
        _collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "WineCoach 长期记忆库，按 user_id 隔离"},
        )
    return _collection
