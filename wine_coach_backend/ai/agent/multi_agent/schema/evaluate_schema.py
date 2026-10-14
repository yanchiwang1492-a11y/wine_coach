"""
评估结构化输出 Schema
"""
from pydantic import BaseModel, Field


class QuestionScore(BaseModel):
    """单题评分（满分 100 = 知识 60 + 技巧 25 + 表达 15）"""
    question: str = Field(..., description="题目原文")
    knowledge_score: int = Field(..., description="专业知识得分（满分60）")
    skill_score: int = Field(..., description="销售技巧得分（满分25）")
    expression_score: int = Field(..., description="表达沟通得分（满分15）")
    total_score: int = Field(..., description="总分（满分100）")


class EvaluateSchema(BaseModel):
    """综合评价结构化输出（供前端 echarts 绘图 + 渲染 Markdown 文字）"""
    scores: list[QuestionScore] = Field(..., description="逐题评分列表")
    advantages: list[str] = Field(..., description="优势（至少1条）")
    disadvantages: list[str] = Field(..., description="劣势（至少1条）")
    suggestions: list[str] = Field(..., description="训练建议（至少1条）")
