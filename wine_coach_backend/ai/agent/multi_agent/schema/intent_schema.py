"""
意图识别 + 路由分类 Schema
"""
from pydantic import BaseModel, Field


class IntentSchema(BaseModel):
    """意图识别结构化输出：5 个筛选维度 + 题目数量 + 出题关键词"""
    question_type: str = Field(..., description="题型：知识 / 话术 / 情景应对 / 产品推荐，未识别输出 不限")
    sales_stage: str = Field(..., description="销售阶段：迎宾 / 需求挖掘 / 推荐 / 异议处理 / 成交 / 售后，未识别输出 不限")
    customer_type: str = Field(..., description="客户画像：新手 / 送礼 / 宴请 / 收藏 / 团购，未识别输出 不限")
    product_category: str = Field(..., description="酒类知识：产区 / 品种 / 年份 / 配餐 / 储存，未识别输出 不限")
    country: str = Field(..., description="国家：法国 / 意大利 / 西班牙 / 德国 / 葡萄牙 / 美国 / 智利 / 阿根廷 / 澳大利亚 / 新西兰 / 南非 / 中国 / 奥地利 / 希腊 / 格鲁吉亚 / 匈牙利 / 罗马尼亚 / 摩尔多瓦 / 乌拉圭 / 巴西，未识别输出 不限")
    question_count: int = Field(..., description="题目数量")
    keywords: list[str] = Field(..., description="从用户画像和用户请求中提炼的 2-4 个出题关键词，用于在题库中做模糊匹配，例如 ['法国酒', '波尔多', '经销商']。如果没有明显关键词输出空数组。")


class RouterSchema(BaseModel):
    """路由分类输出：practice / answer / chat 三类"""
    route: str = Field(..., description="路由分类，只在 practice, answer, chat 三者中选一个")
