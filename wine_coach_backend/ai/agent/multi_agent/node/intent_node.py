"""
意图识别节点
识别用户描述的练习场景：4 个筛选维度 + 题目数量
维度卡片/标签的固定提示词走快速通道（跳过 LLM），自由文本走 LLM 识别
"""
import asyncio
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_agent

from ai.agent.multi_agent.schema.intent_schema import IntentSchema
from ai.agent.multi_agent.state.coach_state import CoachState
from ai.model.my_model import MyModel, LLM_TIMEOUT
from ai.prompt.builder_prompt import BuilderPromptYaml
from memory.memory_save.profile_memory import ProfileMemory, FIELD_LABELS
from memory.memory_retrieval.profile_agent import maybe_update_profile

base_prompt = BuilderPromptYaml.get_prompt("intent_node.yaml")

# 20 个葡萄酒最知名国家（含中国），与题库 country 维度一致
COUNTRY_VALUES = (
    "法国", "意大利", "西班牙", "德国", "葡萄牙", "美国", "智利", "阿根廷",
    "澳大利亚", "新西兰", "南非", "中国", "奥地利", "希腊", "格鲁吉亚",
    "匈牙利", "罗马尼亚", "摩尔多瓦", "乌拉圭", "巴西",
)

# 维度取值（与 question_library 表一致），用于快速通道
_DIM_VALUES = {
    "question_type": ("知识", "话术", "情景应对", "产品推荐"),
    "sales_stage": ("迎宾", "需求挖掘", "推荐", "异议处理", "成交", "售后"),
    "customer_type": ("新手", "送礼", "宴请", "收藏", "团购"),
    "product_category": ("产区", "品种", "年份", "配餐", "储存"),
    "country": COUNTRY_VALUES,
}

_BASE_DIMS = {
    "question_type": "不限",
    "sales_stage": "不限",
    "customer_type": "不限",
    "product_category": "不限",
    "country": "不限",
    "question_count": 1,
}

# 主营酒类国家 → 常见产区/品种词（用于把画像里的国家展开成可匹配题目内容的关键词）
COUNTRY_TO_REGIONS = {
    "法国": ["波尔多", "勃艮第", "香槟", "罗讷河谷", "卢瓦尔", "赤霞珠", "梅洛"],
    "意大利": ["托斯卡纳", "皮埃蒙特", "基安蒂", "巴罗洛", "桑娇维塞"],
    "西班牙": ["里奥哈", "雪莉", "卡瓦", "丹魄"],
    "美国": ["纳帕谷", "加州", "索诺玛"],
    "智利": ["中央山谷", "卡萨布兰卡谷", "佳美娜"],
    "阿根廷": ["马尔贝克", "门多萨"],
    "澳大利亚": ["澳洲", "巴罗萨", "西拉", "麦克拉伦谷"],
    "新西兰": ["马尔堡", "长相思", "黑皮诺"],
    "德国": ["雷司令", "摩泽尔"],
    "中国": ["宁夏", "贺兰山"],
}


def _expand_country_keywords(keywords: list[str]) -> list[str]:
    """把关键词里的国家名展开成对应产区/品种词，便于 LIKE 匹配题目内容（去重保序）"""
    if not keywords:
        return []
    expanded = []
    for kw in keywords:
        expanded.append(kw)
        for country, regions in COUNTRY_TO_REGIONS.items():
            if country in kw:
                expanded.extend(regions)
    seen: set[str] = set()
    result: list[str] = []
    for k in expanded:
        if k and k not in seen:
            seen.add(k)
            result.append(k)
    return result


def _fast_intent(text: str) -> dict | None:
    """从维度卡片/标签的固定提示词直接解析维度，命中返回维度字典，否则 None"""
    m = re.search(r"(\d+)\s*道", text)
    count = int(m.group(1)) if m else 1

    for t in _DIM_VALUES["question_type"]:
        if f"{t}题" in text:
            return {**_BASE_DIMS, "question_type": t, "question_count": count}
    for s in _DIM_VALUES["sales_stage"]:
        if f"{s}阶段" in text:
            return {**_BASE_DIMS, "sales_stage": s, "question_count": count}
    for c in _DIM_VALUES["customer_type"]:
        if f"{c}客户" in text:
            return {**_BASE_DIMS, "customer_type": c, "question_count": count}
    for p in _DIM_VALUES["product_category"]:
        if f"关于{p}" in text:
            return {**_BASE_DIMS, "product_category": p, "question_count": count}
    for c in _DIM_VALUES["country"]:
        if f"关于{c}" in text or f"{c}酒" in text:
            return {**_BASE_DIMS, "country": c, "question_count": count}
    return None


def _profile_to_keywords(profile: dict) -> list[str]:
    """从画像字段里提炼出题关键词（快速通道兜底用）。主营酒类按国家展开成产区词。"""
    kws = []
    pf = profile.get("product_focus", "")
    if pf:
        kws.append(pf)
    cg = profile.get("customer_group", "")
    if cg:
        kws.append(cg)
    goal = profile.get("goal", "")
    if goal:
        kws.append(goal)
    return _expand_country_keywords(kws)


def _apply_profile_country(data: dict, profile: dict, user_input: str) -> bool:
    """画像主营国家映射到 country 维度：用户未明确指定国家时，用画像国家覆盖。返回是否覆盖。"""
    pf = profile.get("product_focus", "")
    if pf not in COUNTRY_VALUES:
        return False
    # 用户明确提到了某个国家（"XX酒"/"关于XX"）→ 尊重用户指定，不覆盖
    for c in COUNTRY_VALUES:
        if f"{c}酒" in user_input or f"关于{c}" in user_input:
            return False
    # 用户未明确指定（如"根据我的情况出题"）→ 用画像国家
    data["country"] = pf
    return True


async def intent_node(state: CoachState) -> dict[str, Any]:
    """识别用户的练习意图，返回筛选维度和题目数量"""
    user_input = state["messages"][-1].content

    # 机会式画像采集：用户消息提及自身情况时静默抽取更新
    await maybe_update_profile(state["user_id"], user_input)

    # 快速通道：维度卡片固定提示词直接映射，跳过 LLM（提速）
    data = _fast_intent(user_input)
    profile = await ProfileMemory(state["user_id"]).load()
    profile_applied = False
    if data is not None:
        data["keywords"] = _profile_to_keywords(profile)
        profile_applied = _apply_profile_country(data, profile, user_input)
    else:
        # 自由文本：LLM 识别 + 全量注入画像背景（补维度 + 出关键词）
        prompt = base_prompt
        if any(profile.values()):
            bg = "；".join(f"{FIELD_LABELS[k]}：{v}" for k, v in profile.items() if v)
            prompt += f"\n\n【用户背景】\n{bg}\n\n请结合用户背景补全模糊维度，并提炼出题关键词。"

        model = MyModel.get_online_model()
        agent = create_agent(model=model, system_prompt=prompt, response_format=IntentSchema)
        rs = await asyncio.wait_for(
            agent.ainvoke({"messages": [HumanMessage(content=user_input)]}),
            timeout=LLM_TIMEOUT,
        )
        data = rs["structured_response"].model_dump()
        profile_applied = _apply_profile_country(data, profile, user_input)

    # 简洁回显：只列非"不限"的维度
    dims = []
    for label, val in [
        ("题型", data["question_type"]),
        ("阶段", data["sales_stage"]),
        ("客户", data["customer_type"]),
        ("知识", data["product_category"]),
        ("国家", data.get("country", "不限")),
    ]:
        if val != "不限":
            dims.append(f"{label}·{val}")
    suffix = f"（{'，'.join(dims)}）" if dims else ""
    ai_msg = f"\n已为你准备 {data['question_count']} 道题{suffix}\n"

    return {
        "messages": [AIMessage(content=ai_msg)],
        "question_type": data["question_type"],
        "sales_stage": data["sales_stage"],
        "customer_type": data["customer_type"],
        "product_category": data["product_category"],
        "country": data.get("country", "不限"),
        "question_count": data["question_count"],
        # 国家由画像覆盖时，关键词也强制来自画像（避免 LLM 幻觉关键词干扰出题）
        "keywords": (
            _profile_to_keywords(profile) if profile_applied
            else _expand_country_keywords(data.get("keywords", []))
        ),
        "profile": profile,
        "practice_step": "intent",
    }
