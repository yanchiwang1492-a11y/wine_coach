from app.ai.agent.multi_agent.state.exam_state import ExamState
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import HumanMessage

"""
主管节点，中枢，负责调用其他节点
"""
def manager_node(state:ExamState):
    #获取考试状态
    exam_state = state.get("exam_step","start")
    print(f"当前考试状态:{exam_state}")
    print(f"状态:{state}")
    #获取用户输入
    last_msg =  state["messages"][-1]
    if isinstance(last_msg, HumanMessage):
        user_input = last_msg.content
    else:
        user_input = ""
    print(f"用户输入:{user_input}")
    #如果是第一次进入
    if exam_state =="start":
        #调用意图识别节点
        return Command(goto="intent")
    elif exam_state =="intent":
        # 调用意图识别节点
        return Command(goto="question")
    elif exam_state == "question":

        # 调用意图识别节点
        return Command(goto=END)





