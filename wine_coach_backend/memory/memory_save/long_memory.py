"""
L3 长期记忆：Chroma 向量库存储（类封装）
每条记录含文本内容 + 元数据（user_id / memory_type / created_at）
"""
import asyncio
import uuid
from datetime import datetime
from typing import Any

from common.chroma_util import get_collection


class LongMemory:
    """长期记忆：Chroma 向量库，按 user_id 隔离，按语义相似度检索（而非关键词）"""

    def __init__(self):
        self._collection = get_collection()

    async def save(
        self,
        user_id: int | str,
        content: str,
        memory_type: str,
    ) -> str:
        """添加一条长期记忆，返回 memory_id"""
        memory_id = f"mem_{uuid.uuid4().hex[:8]}"
        await asyncio.to_thread(
            self._collection.add,
            ids=[memory_id],
            documents=[content],
            metadatas=[{
                "user_id": str(user_id),
                "memory_type": memory_type,
                "created_at": datetime.now().isoformat(),
            }],
        )
        return memory_id

    async def search(
        self,
        user_id: int | str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """向量检索用户的长期记忆

        Returns:
            [{"memory_id": "...", "content": "...", "memory_type": "..."}]
        """
        try:
            results = await asyncio.to_thread(
                self._collection.query,
                query_texts=[query],
                n_results=top_k,
                where={"user_id": str(user_id)},
            )
        except Exception:
            return []

        memories = []
        if results and results["documents"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            for i, doc in enumerate(docs):
                memories.append({
                    "memory_id": ids[i],
                    "content": doc,
                    "memory_type": metas[i]["memory_type"],
                })
        return memories
