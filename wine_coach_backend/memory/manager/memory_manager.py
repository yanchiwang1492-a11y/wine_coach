"""
记忆管理器：统一调度两层记忆的更新（L1 窗口每条消息更新，L2 摘要窗口满时更新）。
集中管理触发时机，业务代码只需调用一个函数。
"""
from memory.manager.session_manager import SessionManager
from memory.memory_retrieval.summary_agent import SummaryAgent

WINDOW_TRIGGER = 10  # 窗口 ≥ 10 条时触发 L2 摘要


class MemoryManager:
    """记忆更新调度器：决定什么时候更新哪一层记忆"""

    def __init__(self, session: SessionManager):
        self.session = session
        self.summary_agent = SummaryAgent(session.summary_memory)

    async def on_user_message(self, role: str, content: str) -> None:
        """用户消息写入后调用：写入 L1 窗口"""
        await self.session.save(role, content)

    async def on_ai_reply(self, reply_content: str) -> None:
        """
        AI 回复后调用：
        - 写入 L1 窗口
        - 窗口满时触发 L2 摘要
        """
        await self.session.save("assistant", reply_content)

        # L2 摘要（窗口满触发）
        messages = await self.session.window_memory.load()
        if len(messages) >= WINDOW_TRIGGER:
            await self.summary_agent.update(messages, self.session.user_id)
            await self.session.window_memory.clear()
