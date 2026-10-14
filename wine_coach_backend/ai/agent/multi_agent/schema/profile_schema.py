"""
用户画像结构化输出 Schema（红酒销售领域）
"""
from pydantic import BaseModel, Field


class ProfileSchema(BaseModel):
    """红酒销售画像：5 字段，未提及留空。取值与题库维度对齐，便于画像直接驱动出题。"""

    company_type: str = Field(default="", description="公司类型：品牌方/经销商/烟酒店/商超/电商平台，未提及留空")
    sales_channel: str = Field(default="", description="销售渠道：门店/线上电商/直播/电话/大客户，未提及留空")
    product_focus: str = Field(default="", description="主营国家：法国/意大利/西班牙/德国/葡萄牙/美国/智利/阿根廷/澳大利亚/新西兰/南非/中国/奥地利/希腊/格鲁吉亚/匈牙利/罗马尼亚/摩尔多瓦/乌拉圭/巴西，未提及留空（用户说'国产酒/国内酒'时填'中国'）")
    customer_group: str = Field(default="", description="主要客户：新手/送礼/宴请/收藏/团购（与题库客户画像维度一致），未提及留空")
    goal: str = Field(default="", description="提升目标：成交率/客单价/话术/异议处理/产品知识，未提及留空")
