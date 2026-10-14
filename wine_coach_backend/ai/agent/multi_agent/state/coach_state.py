"""
练习状态定义
"""
import operator
from typing import Any

from typing_extensions import TypedDict, Annotated
from langchain_core.messages import AnyMessage


class CoachState(TypedDict):
    # ---------- 消息列表（operator.add 累积） ----------
    messages: Annotated[list[AnyMessage], operator.add]

    # ---------- 用户信息 ----------
    user_id: str  # 用户 ID（从 graph.chat 传入，供记忆系统使用）
    session_id: str  # 会话 ID（从 graph.chat 传入，供记忆上下文使用）

    # ---------- 意图识别输出 ----------
    question_type: str       # 题型：知识/话术/情景应对/产品推荐/不限
    sales_stage: str         # 销售阶段
    customer_type: str       # 客户画像
    product_category: str    # 酒类知识
    country: str             # 国家：法国/意大利/.../中国/不限
    question_count: int      # 题目总数
    keywords: list[str]      # 画像/意图提炼的出题关键词（如 ["法国酒", "波尔多"]）

    # ---------- 用户画像（L4，从 Redis 同步入 state 供前端展示） ----------
    profile: dict[str, str]  # {company_type, sales_channel, product_focus, customer_group, goal}

    # ---------- 出题输出 ----------
    questions: list[dict[str, Any]]   # 已出题目列表 [{id, question, answer, ...}]

    # ---------- 答题输出 ----------
    user_answer_list: list[dict[str, Any]]  # 用户答案列表 [{id, answer}]

    # ---------- 进度 ----------
    current_index: int    # 当前已答题数

    # ---------- 评价输出 ----------
    evaluation: str                    # 完整评价文本（Markdown，供阅读/邮件正文）
    evaluation_detail: list[dict[str, Any]]  # 结构化评分（供前端 echarts 绘图）

    # ---------- 流程控制 ----------
    practice_step: str     # 流程状态：start/intent/question/answer/evaluate/done
    question_id: int       # 当前题目 ID
    continue_question: bool  # 是否继续出题
