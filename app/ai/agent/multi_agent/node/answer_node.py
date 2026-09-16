from langchain_core.messages import HumanMessage, AIMessage

from app.ai.agent.multi_agent.state.exam_state import ExamState

"""
答题节点：收集用户答案，判断下一个节点 是去评价还是继续出题
"""
def answer_node(state:ExamState):
    #获取用户答案
    last_msg =  state["messages"][-1]
    if isinstance(last_msg, HumanMessage):
        user_input = last_msg.content
        #获取当前题目的编号
        question_id = state["question_id"]
        #获取用户答案列表
        user_answer_list = state.get("user_answer_list",[])
        #添加答案道答案列表
        user_answer_list.append(
            {"id":question_id,"answer":user_input}
        )
        #获取题目索引和题目数量
        current = state["current"]
        total = state["total"]
        print(f"当前题目:{current}，总题目数:{total}")
        #判断是否继续出题
        if current < total:
            print("继续出题")
            continue_question = True
        else:
            print("所有题目已答完，进入评价")
            #下一个节点是评价
            continue_question = False
        return {
            "messages":[AIMessage(content="\n答案已经记录\n")],
            "user_answer_list":user_answer_list,
            "exam_step":"answer",
            "continue_question":continue_question
        }
    else:
        return {
            "messages": [AIMessage(content="\n不是用户输入\n")],
        }
