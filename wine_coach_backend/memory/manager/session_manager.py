"""
会话管理器：四层记忆对象的创建、写入、提示词构建的统一入口。
封装「组合操作」，对外只暴露 save / build_prompt 两个接口。
"""
from memory.memory_save.window_memory import WindowMemory
from memory.memory_save.summary_memory import SummaryMemory
from memory.memory_save.long_memory import LongMemory
from memory.memory_save.profile_memory import ProfileMemory
from memory.manager.prompt_builder import PromptBuilder


class SessionManager:
    """会话级记忆管理器：一个 session_id 对应一个 SessionManager 实例"""

    def __init__(self, session_id: str, user_id: int):
        self.session_id = session_id
        self.user_id = user_id

        # 四层记忆存储对象
        self.window_memory = WindowMemory(session_id)
        self.summary_memory = SummaryMemory(session_id)
        self.long_memory = LongMemory()
        self.profile_memory = ProfileMemory(user_id)

        # prompt 构建器
        self.prompt_builder = PromptBuilder(self)

    async def save(self, role: str, content: str) -> None:
        """写入一条消息到 L1 窗口记忆"""
        await self.window_memory.save(role, content)

    async def build_prompt(self, current_question: str) -> str:
        """
        组装四层记忆为 system prompt

        组装顺序：L2摘要 → L3长期Top5 → L4画像 → L1窗口
        """
        return await self.prompt_builder.build(current_question)
