"""
L2 摘要 Agent：根据窗口消息生成会话摘要（类封装）
触发条件：窗口消息 ≥ N 条时调用
"""
import asyncio

from ai.model.my_model import MyModel, LLM_TIMEOUT
from memory.memory_save.summary_memory import SummaryMemory
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage


class SummaryAgent:
    """摘要生成 Agent：读旧摘要 + 新对话 → 生成新摘要"""

    PROMPT_TEMPLATE = """你是一个对话摘要助手。请根据以下对话历史，生成一段简短的摘要。

要求：
- 保留关键信息（用户练习了什么题型、薄弱点、评分情况等）
- 去除闲聊和礼貌性对话
- 控制在 200 字以内
- 用第三人称叙述

对话历史：
{history}

请输出摘要："""

    def __init__(self, summary_memory: SummaryMemory):
        self.summary_memory = summary_memory

    def _render(self, old_summary: str, messages: list[dict]) -> str:
        lines = [
            f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in messages
        ]
        history = "\n".join(lines)
        if old_summary:
            history = f"【历史摘要】{old_summary}\n\n【新对话】\n{history}"
        return self.PROMPT_TEMPLATE.format(history=history)

    async def update(self, messages: list[dict], user_id: int) -> str:
        """增量生成新摘要并存入 PG"""
        old_summary = await self.summary_memory.load(user_id)
        prompt = self._render(old_summary, messages)

        model = MyModel.get_online_model()
        agent = create_agent(model=model, system_prompt="")
        result = await asyncio.wait_for(
            agent.ainvoke({"messages": [HumanMessage(content=prompt)]}),
            timeout=LLM_TIMEOUT,
        )
        reply = result["messages"][-1].content.strip()

        await self.summary_memory.save(user_id, reply)
        print(f"[SummaryAgent] L2 摘要已更新: {reply[:50]}…")
        return reply
