"""
评价节点：对所有答案做综合评价，结构化输出 + 流式输出 Markdown 文本
"""
import asyncio
from typing import Any
from langchain_core.messages import HumanMessage, AIMessage
from ai.model.my_model import MyModel
from ai.agent.multi_agent.state.coach_state import CoachState
from ai.agent.multi_agent.schema.evaluate_schema import EvaluateSchema
from ai.prompt.builder_prompt import BuilderPromptYaml
from langchain.agents import create_agent
from langgraph.config import get_stream_writer

from memory.memory_save.long_memory import LongMemory

# 预加载提示词
prompt = BuilderPromptYaml.get_prompt("evaluate_node.yaml")


def _render_markdown(data: dict) -> str:
    """把结构化评分渲染成 Markdown 文本（供前端阅读 + 邮件正文）"""
    lines = ["## 综合评价报告\n"]
    for i, s in enumerate(data["scores"], 1):
        lines.append(f"### 第{i}题：{s['question']}")
        lines.append(f"- 专业知识：{s['knowledge_score']} / 60")
        lines.append(f"- 销售技巧：{s['skill_score']} / 25")
        lines.append(f"- 表达沟通：{s['expression_score']} / 15")
        lines.append(f"- **总分：{s['total_score']} / 100**\n")
    lines.append("### 整体评价")
    if data["advantages"]:
        lines.append("\n**优势**")
        lines.extend(f"- {a}" for a in data["advantages"])
    if data["disadvantages"]:
        lines.append("\n**劣势**")
        lines.extend(f"- {d}" for d in data["disadvantages"])
    if data["suggestions"]:
        lines.append("\n**训练建议**")
        lines.extend(f"- {s}" for s in data["suggestions"])
    return "\n".join(lines)


async def evaluate_node(state: CoachState) -> dict[str, Any]:
    """对用户所有答案做综合评价（线上模型结构化输出）"""
    question_list = state["questions"]
    user_answer_list = state["user_answer_list"]
    eval_input = f"实战题目列表:{question_list}\n用户作答列表:{user_answer_list}"

    write = get_stream_writer()

    model = MyModel.get_online_model()
    agent = create_agent(model=model, system_prompt=prompt, response_format=EvaluateSchema)
    # user_msg = {"messages": {"role": "user", "content": eval_input}}
    user_msg = {"messages": [HumanMessage(content=eval_input)]}
    # rs = await asyncio.wait_for(agent.ainvoke(user_msg), timeout=30) 如果这样写需要兜底
    rs = await agent.ainvoke(user_msg)
    data = rs["structured_response"].model_dump()
    evaluation_detail = data["scores"]
    evaluation_text = _render_markdown(data)
    write(evaluation_text)

    # 存入长期记忆（每题一条：问题 + 用户答案 + 评分）
    if evaluation_detail and question_list:
        long_mem = LongMemory()
        user_id = int(state["user_id"])
        answers = {a.get("id"): a.get("answer", "") for a in user_answer_list}
        for i, score in enumerate(evaluation_detail):
            q = question_list[i] if i < len(question_list) else None
            if not q:
                continue
            user_ans = answers.get(q["id"], "")
            content = (
                f"题型：{q['question_type']} / 阶段：{q['sales_stage']}\n"
                f"题目：{q['question']}\n"
                f"用户答案：{user_ans}\n"
                f"评分：知识{score['knowledge_score']}/60，"
                f"技巧{score['skill_score']}/25，"
                f"表达{score['expression_score']}/15，"
                f"总分{score['total_score']}/100"
            )
            await long_mem.save(user_id, content, memory_type="practice_question")

    # 正文已通过 stream_writer 流出，返回空内容避免 messages 模式二次输出
    return {
        "messages": [AIMessage(content="")],
        "evaluation": evaluation_text,
        "evaluation_detail": evaluation_detail,
        "practice_step": "done",
    }
