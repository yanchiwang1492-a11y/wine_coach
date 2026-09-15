from app.ai.agent.multi_agent.state.exam_state import ExamState
from app.ai.agent.multi_agent.node.intent_node import intent_node
from app.ai.agent.multi_agent.node.question_node import question_node
from langgraph.graph import StateGraph,START,END
from langchain_core.messages import HumanMessage
import asyncio
"""
模拟面试智能体
"""
class ExamGraph:

    def __init__(self):
        self.agent = self.get_agent()

   #构建图
    def get_agent(self):
        graph = StateGraph(ExamState)
        #添加节点
        graph.add_node("intent",intent_node)
        graph.add_node("question",question_node)

        #画边
        graph.add_edge(START,"intent")
        graph.add_edge("intent","question")
        graph.add_edge("question",END)
        #编译
        self.agent = graph.compile()
        return self.agent
    #对话
    async def chat(self,question,user_id,session_id):
        #构建用户问题
        user_msg ={"messages":[HumanMessage(content=question)]}
        #采用异步流式
        async for c,m in self.agent.astream(user_msg,stream_mode="messages"):
            if c.content:
                yield c.content
    #画图
    def draw(self):
        data = self.agent.get_graph().draw_mermaid_png()
        with open("考试图.png","wb") as f:
            f.write(data)
if __name__ =="__main__":
    # exam_graph = ExamGraph()
    # exam_graph.draw()
    q1="给我3道java题目"
    q2="给我几道面试题"
    async def test():
        agent = ExamGraph()
        async  for c in agent.chat(q1,"1","001"):
            print(c,end="")
    asyncio.run(test())













