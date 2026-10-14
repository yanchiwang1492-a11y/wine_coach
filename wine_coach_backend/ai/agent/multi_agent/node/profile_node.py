"""
画像采集节点：抽取用户自述中的画像写入 L4，简洁回显并写入 state。
仅由 manager 在「纯画像描述」时路由进入。
画像详情由前端「销冠画像」顶部 chip 展示，节点只回显"已更新 + 询问是否出题"。
"""
from typing import Any

from langchain_core.messages import AIMessage

from ai.agent.multi_agent.state.coach_state import CoachState
from memory.memory_retrieval.profile_agent import ProfileAgent
from memory.memory_save.profile_memory import ProfileMemory

RETRY = "\n我还没get到你的情况～能再具体点吗？比如你是做什么渠道的、主营哪国酒、客户群体是怎样的？\n"


async def profile_node(state: CoachState) -> dict[str, Any]:
    """抽取用户自述中的画像，写入 L4 并简洁回显确认"""
    user_input = state["messages"][-1].content
    data = await ProfileAgent().extract(user_input)
    non_empty = {k: v for k, v in data.items() if v}

    if not non_empty:
        return {"messages": [AIMessage(content=RETRY)], "practice_step": "start"}

    user_id = state["user_id"]
    await ProfileMemory(user_id).update(non_empty)
    full_profile = await ProfileMemory(user_id).load()

    return {
        "messages": [AIMessage(content="✅ 画像已更新。\n\n需要我根据你的情况给你出一道题吗？")],
        "profile": full_profile,
        "practice_step": "start",
    }
