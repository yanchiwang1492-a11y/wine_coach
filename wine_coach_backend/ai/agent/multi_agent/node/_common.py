"""
图节点共享常量与工具函数
"""

# 查看答案类关键词：走 chat 节点，返回参考答案、不推进练习状态
VIEW_ANSWER_KEYWORDS = ("查看答案", "参考答案", "给答案", "答案是什么")

# 未作答类关键词：走 answer 节点，标记为未作答
UNANSWERED_KEYWORDS = ("我不会", "不知道")


def get_current_answer(questions: list, current_index: int) -> str:
    """获取当前题目的参考答案，越界或为空返回空串"""
    if questions and 0 < current_index <= len(questions):
        return questions[current_index - 1]["answer"]
    return ""
