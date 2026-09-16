from app.ai.agent.multi_agent.state.exam_state import ExamState
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import HumanMessage

"""
主管节点，中枢，负责调用其他节点
"""
def manager_node(state:ExamState):
    #获取是否继续出题
    continue_question = state.get("continue_question",True)
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
        if  user_input =="":
            print("等待用户输入答案")
            return Command(goto=END)
        else:
            #进入答案节点
            return Command(goto="answer")
    elif exam_state == "answer":
        if continue_question:
            print("继续出题")
            return Command(goto="question")
        else:
            print("答案结束")
            return Command(goto="evaluate")
    elif exam_state == "evaluate":
        # 调用意图识别节点
        return Command(goto="evaluate")
    elif exam_state == "done": #评价结束
        # 调用意图识别节点
        return Command(goto=END)
    else:
        return Command(goto=END)





