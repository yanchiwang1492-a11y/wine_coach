"""
记忆组装器：PromptBuilder，把四层记忆组装进 system prompt，注入到 chat/evaluate 节点。
为避免循环导入，文件顶部不 import SessionManager，运行时通过 self.session 使用。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from memory.memory_save.profile_memory import FIELD_LABELS

if TYPE_CHECKING:
    from memory.manager.session_manager import SessionManager


class PromptBuilder:
    """四层记忆 → 一段 system prompt 文本。
    拼接顺序：摘要（大局观）→ 长期记忆/画像（稳定知识）→ 最近对话（最贴合当下），
    利用模型对 prompt 首尾更敏感的特性。
    """

    def __init__(self, session: SessionManager):
        self.session = session

    async def build(self, current_question: str = "") -> str:
        """
        组装四层记忆上下文，拼接成一段文本

        组装顺序：L2摘要 → L3长期Top5 → L4画像 → L1窗口
        """
        parts = []

        # L2 摘要（当前会话）
        summary = await self.session.summary_memory.load(self.session.user_id)
        if summary:
            parts.append(f"【历史摘要】\n{summary}")

        # L3 长期记忆（Top 5）
        if current_question:
            memories = await self.session.long_memory.search(
                self.session.user_id, current_question, top_k=5
            )
            if memories:
                mem_text = "\n".join(f"- {m['content']}" for m in memories)
                parts.append(f"【相关长期记忆】\n{mem_text}")

        # L4 用户画像（跨会话）
        profile = await self.session.profile_memory.load()
        profile_lines = [f"{FIELD_LABELS[k]}：{profile[k]}" for k in profile if profile[k]]
        if profile_lines:
            parts.append("【用户画像】\n" + "；".join(profile_lines))

        # L1 窗口（最近 10 条）
        window = await self.session.window_memory.load()
        if window:
            window_text = "\n".join(
                f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in window[-10:]
                # 在没满10条就压缩一次的逻辑下，等价于for m in window
            )
            parts.append(f"【最近对话】\n{window_text}")

        if not parts:
            return ""

        return "\n\n".join(parts) + "\n\n"
