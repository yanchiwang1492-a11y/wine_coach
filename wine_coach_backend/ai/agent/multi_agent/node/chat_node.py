"""
聊天节点：处理闲聊、历史追问、记忆问答、评估报告邮件发送
"""
import asyncio
import re
from typing import Any

from langchain_core.messages import AIMessage
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langgraph.config import get_stream_writer

from ai.model.my_model import MyModel
from ai.agent.multi_agent.state.coach_state import CoachState
from ai.prompt.builder_prompt import BuilderPromptYaml
from ai.tool.send_email_tool import send_email
from ai.agent.multi_agent.node._common import get_current_answer, VIEW_ANSWER_KEYWORDS
from memory.manager.session_manager import SessionManager
from memory.memory_retrieval.profile_agent import maybe_update_profile
from memory.memory_save.profile_memory import ProfileMemory

prompt_template = BuilderPromptYaml.get_prompt("chat_node.yaml")

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# -：字面量减号（放在最后，不会被当成范围）


async def chat_node(state: CoachState) -> dict[str, Any]:
    """聊天 + 历史记忆 + 评估报告发邮件"""
    messages = state["messages"]
    user_id = state["user_id"]
    session_id = state["session_id"]
    evaluation = state.get("evaluation", "")

    last_user_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            last_user_msg = msg.content
            break

    # 机会式画像采集：闲聊中提及自身情况时静默抽取更新
    await maybe_update_profile(user_id, last_user_msg)
    profile = await ProfileMemory(user_id).load()

    # 查看答案：返回参考答案后，本轮练习视为结束，重置为 done
    # （避免用户接下来说话被当成"答案"继续走答题状态机）
    if any(kw in last_user_msg for kw in VIEW_ANSWER_KEYWORDS):
        answer = get_current_answer(state.get("questions", []), state.get("current_index", 0))
        return {
            "messages": [AIMessage(content=f"\n参考答案：{answer}\n")],
            "profile": profile,
            "practice_step": "done",
        }

    # 发送评估报告：消息里含邮箱时直接发送，不依赖大模型工具调用
    if evaluation:
        m = EMAIL_RE.search(last_user_msg)
        if m:
            result = await asyncio.to_thread(
                send_email, m.group(0), "WineCoach 练习评估报告", evaluation
            )
            return {
                "messages": [AIMessage(content=f"\n{result}\n")],
                "profile": profile,
                "practice_step": "done",
            }

    # 组装记忆上下文
    session = SessionManager(session_id, int(user_id))
    memory_context = await session.build_prompt(last_user_msg)
    system_prompt = memory_context + prompt_template if memory_context else prompt_template

    write = get_stream_writer()
    agent = create_agent(
        model=MyModel.get_online_model(),
        system_prompt=system_prompt,
        middleware=[ModelCallLimitMiddleware(thread_limit=3, exit_behavior="end")],
    )
    full_text = []
    async for c, _ in agent.astream({"messages": messages}, stream_mode="messages"):
        if c.content:
            full_text.append(c.content)
            write(c.content)
    reply_text = "".join(full_text)

    if not reply_text:
        reply_text = "\n抱歉，我暂时无法回答这个问题，请稍后再试。\n"
        write(reply_text)

    # 正文已通过 stream_writer 流出，返回空内容避免 messages 模式二次输出
    return {"messages": [AIMessage(content="")], "profile": profile, "practice_step": "done"}
