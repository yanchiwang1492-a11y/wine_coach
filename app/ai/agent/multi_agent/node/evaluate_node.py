from langchain_core.messages import HumanMessage, AIMessage

from app.ai.agent.multi_agent.state.exam_state import ExamState

"""
评价节点
"""
def evaluate_node(state:ExamState):
    ai_msg="\n开始评价\n"
    return {
        "messages":[AIMessage(content=ai_msg)],
        "exam_step":"done"#评价完成
    }