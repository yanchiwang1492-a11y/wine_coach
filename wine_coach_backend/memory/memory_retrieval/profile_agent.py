"""
L4 画像提取 Agent：从用户对自身销售情况的描述中抽取结构化画像
"""
import asyncio

from ai.model.my_model import MyModel, LLM_TIMEOUT
from ai.agent.multi_agent.schema.profile_schema import ProfileSchema
from memory.memory_save.profile_memory import ProfileMemory
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

EXTRACT_PROMPT = """你是红酒销售教练的画像提取助手。根据用户对自己销售情况的自然语言描述，提取结构化画像。

规则：
1. 只提取用户明确说出的信息，不要编造、不要推测、不要补全
2. 未提及的字段一律留空字符串
3. 用户可能用一句话描述（如"我在烟酒店做门店销售，主要卖法国酒，客户多是送礼的"），需映射到对应字段

字段说明（取值与题库分类维度对齐）：
- company_type 公司类型：品牌方/经销商/烟酒店/商超/电商平台
- sales_channel 销售渠道：门店/线上电商/直播/电话/大客户
- product_focus 主营国家：法国/意大利/西班牙/德国/葡萄牙/美国/智利/阿根廷/澳大利亚/新西兰/南非/中国/奥地利/希腊/格鲁吉亚/匈牙利/罗马尼亚/摩尔多瓦/乌拉圭/巴西。用户说"卖美国酒""做法国酒""主营意大利酒"时，提取对应国家名；说"国产酒""中国酒""国内酒"时提取"中国"；说"波尔多""勃艮第""纳帕谷"等产区时归入其所在国家（波尔多→法国，纳帕谷→美国，巴罗萨→澳大利亚）
- customer_group 主要客户：新手/送礼/宴请/收藏/团购（与题库客户画像维度一致）
- goal 提升目标：成交率/客单价/话术/异议处理/产品知识
"""

# 画像自述信号词：命中才做机会式抽取，避免把出题/答题请求误抽成画像
PROFILE_SIGNAL_KEYWORDS = (
    "我在", "我是", "我做", "我从事", "我目前", "我这边",
    "我们公司", "我的情况", "介绍我的情况",
    "我主要", "主要卖", "我们主要", "主营", "主要做",
)


def has_profile_signal(text: str) -> bool:
    """判断文本是否像用户在描述自身销售情况"""
    return any(kw in text for kw in PROFILE_SIGNAL_KEYWORDS)


class ProfileAgent:
    """画像提取智能体：用户自述 → 结构化画像 dict"""

    async def extract(self, description: str) -> dict:
        model = MyModel.get_online_model()
        agent = create_agent(model=model, system_prompt=EXTRACT_PROMPT, response_format=ProfileSchema)
        rs = await asyncio.wait_for(
            agent.ainvoke({"messages": [HumanMessage(content=description)]}),
            timeout=LLM_TIMEOUT,
        )
        return rs["structured_response"].model_dump()


async def maybe_update_profile(user_id: str, text: str) -> None:
    """机会式画像采集：文本含自述信号时抽取并静默更新画像"""
    if not has_profile_signal(text):
        return
    data = await ProfileAgent().extract(text)
    non_empty = {k: v for k, v in data.items() if v}
    if non_empty:
        await ProfileMemory(user_id).update(non_empty)
