"""
出题节点：从题库按维度随机抽取一道未出过的题
"""
import asyncio
from typing import Any

from langchain_core.messages import AIMessage

from ai.agent.multi_agent.state.coach_state import CoachState
from ai.tool.question_tool import query_question


async def question_node(state: CoachState) -> dict[str, Any]:
    """
    根据筛选维度从题库随机出一道题

    抽题逻辑（含三级兜底）已下沉到 tools/question_tool.query_question
    """
    question_count = state["question_count"]
    question_list = state.get("questions", [])
    current_index = state.get("current_index", 0) + 1

    # 排除已出过的题
    exclude_ids = [q["id"] for q in question_list]

    keywords = state.get("keywords", [])
    result = await asyncio.to_thread(
        query_question,
        question_type=state["question_type"],
        sales_stage=state["sales_stage"],
        customer_type=state["customer_type"],
        product_category=state["product_category"],
        country=state.get("country", "不限"),
        exclude_ids=exclude_ids,
        keywords=keywords,
    )

    # 题库空
    if not result["found"]:
        return {
            "messages": [AIMessage(content="\n题库暂无可用题目，请稍后再试。\n")],
            "practice_step": "done",
        }

    # 记录题目并生成回复
    question = result["question"]
    question_list.append(question)
    ai_msg = f"\n第{current_index}题:{question['question']}\n"

    return {
        "messages": [AIMessage(content=ai_msg)],
        "questions": question_list,
        "question_count": question_count,
        "current_index": current_index,
        "question_id": question["id"],
        "practice_step": "question",
    }
