"""
答题节点：收集用户答案，判断继续出题还是进入评价
"""
from typing import Any
from langchain_core.messages import AIMessage
from ai.agent.multi_agent.state.coach_state import CoachState
from ai.agent.multi_agent.node._common import get_current_answer, UNANSWERED_KEYWORDS


async def answer_node(state: CoachState) -> dict[str, Any]:
    """
    接收用户答案，记录到答案列表，判断下一轮是继续出题还是进入评价

    支持两种输入：
    - 正常回答 → 记录答案，回复"答案已经记录"
    - 查看答案（"参考答案/我不会/给答案"等）→ 返回当前题目的参考答案
    """
    user_input = state["messages"][-1].content
    question_id = state["question_id"]
    user_answer_list = state.get("user_answer_list", [])

    # 未作答（"我不会/不知道"等）：返回参考答案并标记
    is_view_answer = any(kw in user_input for kw in UNANSWERED_KEYWORDS)

    if is_view_answer:
        answer = get_current_answer(state.get("questions", []), state.get("current_index", 0))
        user_answer_list.append({"id": question_id, "answer": f"[未作答]{user_input}"})
        reply = f"\n参考答案：{answer}\n"
    else:
        # 正常记录用户答案
        user_answer_list.append({"id": question_id, "answer": user_input})
        reply = "\n答案已经记录\n"

    # ========== 功能模块：判断是否还有下一题 ==========
    current_index = state["current_index"]
    question_count = state["question_count"]
    continue_question = current_index < question_count

    return {
        "messages": [AIMessage(content=reply)],
        "user_answer_list": user_answer_list,
        "practice_step": "answer",
        "continue_question": continue_question,
    }
