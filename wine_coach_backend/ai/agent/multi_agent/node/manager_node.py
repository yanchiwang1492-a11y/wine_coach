"""
主管节点（manager）：中央调度器
调度优先级：关键词短路 → router_agent 分类 → practice_step 状态机
"""
from typing import Any
from ai.agent.multi_agent.state.coach_state import CoachState
from ai.agent.multi_agent.node.router_agent import router_agent
from ai.agent.multi_agent.node._common import VIEW_ANSWER_KEYWORDS, UNANSWERED_KEYWORDS
from memory.memory_retrieval.profile_agent import has_profile_signal
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import HumanMessage

# 关键词短路列表（命中直接跳对应节点，不走大模型路由，更快）
KEYWORD_TO_NODE = {kw: "chat" for kw in VIEW_ANSWER_KEYWORDS}
KEYWORD_TO_NODE.update({kw: "answer" for kw in UNANSWERED_KEYWORDS})
KEYWORD_TO_NODE.update({"上一题": "chat", "上一个问题": "chat", "刚刚那道题": "chat"})

# 出题意图关键词：用于区分「纯画像描述」与「出题请求」
PRACTICE_KEYWORDS = ("题", "练习", "训练", "出题", "抽题")


def _match_keyword(text: str) -> str | None:
    """关键词匹配，返回对应节点名或 None"""
    for kw, node in KEYWORD_TO_NODE.items():
        if kw in text:
            return node
    return None


async def manager_node(state: CoachState) -> Command:
    """
    中央调度：决定下一个去哪个节点

    状态机流转：
    - start → intent（识别意图）/ profile（纯画像描述时记录画像）
    - intent → question（出题）
    - question → 用户回答走 answer / AI 出题完成走 END
    - answer → 继续出题走 question / 答完走 evaluate
    - evaluate → done
    - done → 用户新消息走路由（新练习/聊天）
    """
    continue_question = state.get("continue_question", True)
    practice_step = state.get("practice_step", "start")

    last_msg = state["messages"][-1]
    is_user_msg = isinstance(last_msg, HumanMessage)
    user_input = last_msg.content if is_user_msg else ""

    # 纯画像自述：任何状态下（答题中除外）优先走 profile 节点，立即回显"画像已更新"
    # （覆盖 start / done 等状态，避免画像自述被 router 误分到 chat 导致空回复）
    if (
        is_user_msg
        and practice_step != "question"
        and has_profile_signal(user_input)
        and not any(kw in user_input for kw in PRACTICE_KEYWORDS)
    ):
        return Command(goto="profile")

    # 0. 首次进入：非画像描述 → 意图识别
    if practice_step == "start":
        if not is_user_msg:
            return Command(goto=END)
        return Command(goto="intent")

    # 1. 出题后等待回答：用户消息直接走答题（不做路由分类，避免误判为新练习）
    if practice_step == "question" and is_user_msg:
        # 换一题：移除当前题，重新出同维度新题（编号不变）
        if any(kw in user_input for kw in ["换一题", "换题", "再来一题"]):
            questions = state.get("questions", [])
            current_index = state.get("current_index", 0)
            if questions:
                questions.pop()
            return Command(goto="question", update={
                "questions": questions,
                "current_index": max(0, current_index - 1),
            })
        kw_node = _match_keyword(user_input)
        if kw_node:
            return Command(goto=kw_node)
        return Command(goto="answer")

    # 2. 一轮结束（done）：用户新消息走路由分类（新练习/聊天/追问）
    if practice_step == "done" and is_user_msg:
        kw_node = _match_keyword(user_input)
        if kw_node:
            return Command(goto=kw_node)
        route = await router_agent(user_input)
        if route == "practice":
            return Command(goto="intent", update=_reset_state())
        elif route == "answer":
            return Command(goto="answer")
        elif route == "chat":
            return Command(goto="chat")

    # 3. 状态机推进（AI 消息）
    if practice_step == "intent":
        return Command(goto="question")
    elif practice_step == "question":
        return Command(goto=END)
    elif practice_step == "answer":
        if continue_question:
            return Command(goto="question")
        else:
            return Command(goto="evaluate")
    elif practice_step == "evaluate":
        return Command(goto=END)
    elif practice_step == "done":
        return Command(goto=END)

    return Command(goto=END)


def _reset_state() -> dict[str, Any]:
    """重置练习状态（保留 messages），开始新一轮"""
    return {
        "question_type": "不限",
        "sales_stage": "不限",
        "customer_type": "不限",
        "product_category": "不限",
        "country": "不限",
        "question_count": 0,
        "keywords": [],
        "questions": [],
        "user_answer_list": [],
        "current_index": 0,
        "evaluation": "",
        "question_id": 0,
        "continue_question": True,
        "practice_step": "start",
    }
