"""
练习聊天服务层：调用 LangGraph + 记忆系统，产出结构化事件流
"""
import asyncio
from typing import AsyncGenerator

from ai.agent.multi_agent.graph.coach_graph import WineCoachGraph
from ai.tool.history_tool import save_message, update_session_title
from memory.manager.session_manager import SessionManager
from memory.manager.memory_manager import MemoryManager
from common.redis_lock import session_lock


async def stream_chat(
    question: str,
    user_id: int,
    session_id: str,
    coach_agent: WineCoachGraph,
) -> AsyncGenerator[dict, None]:
    """
    流式练习对话，产出结构化事件（status / token / done）

    同一 session 同一时刻只允许一个请求处理（分布式锁保证并发安全）。

    Yields:
        {"kind": "status", "text": "..."}   # 后台状态提示
        {"kind": "token",  "text": "..."}   # 回答文本片段
        {"kind": "done"}                    # 结束标记
    """
    full_text: list[str] = []

    async with session_lock(session_id):
        # 构建会话记忆管理器
        session = SessionManager(session_id, user_id)
        memory_mgr = MemoryManager(session)

        # 保存用户消息 + L1 窗口记忆写入
        await asyncio.to_thread(save_message, session_id, user_id, "user", question)
        await memory_mgr.on_user_message("user", question)

        # 逐事件转发，同时收集 token 拼出完整回复
        async for event in coach_agent.chat_events(question, str(user_id), session_id):
            if event["kind"] == "token":
                full_text.append(event["text"])
            yield event

        # 保存 AI 回复
        full_reply = "".join(full_text)
        await asyncio.to_thread(save_message, session_id, user_id, "assistant", full_reply)

        # L1 窗口记忆 + L2 摘要（窗口满时触发）
        await memory_mgr.on_ai_reply(full_reply)

        # 更新会话标题（取首条用户消息前15字）
        new_title = question[:15] + "…" if len(question) > 15 else question
        await asyncio.to_thread(update_session_title, session_id, user_id, new_title)

    yield {"kind": "done"}
