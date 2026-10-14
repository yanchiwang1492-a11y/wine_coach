"""
WineCoach 练习智能体：LangGraph 六节点图
节点：manager(调度) / intent(意图) / question(出题) / answer(答题) / evaluate(评价) / chat(聊天)
router 为 manager 内部调用的分类函数，非图节点
"""
from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage

from ai.agent.multi_agent.state.coach_state import CoachState
from ai.agent.multi_agent.node.manager_node import manager_node
from ai.agent.multi_agent.node.intent_node import intent_node
from ai.agent.multi_agent.node.question_node import question_node
from ai.agent.multi_agent.node.answer_node import answer_node
from ai.agent.multi_agent.node.evaluate_node import evaluate_node
from ai.agent.multi_agent.node.chat_node import chat_node
from ai.agent.multi_agent.node.profile_node import profile_node

# 节点 → 前端"后台正在干嘛"的阶段提示文案
# manager 是中枢调度节点（每个业务节点都回连它），不产提示，避免刷屏
NODE_STATUS = {
    "profile": "🧭 正在了解你的情况…",
    "intent": "🧭 正在识别你的练习意图…",
    "question": "📚 正在从题库抽取题目…",
    "answer": "📝 正在记录你的答案…",
    "evaluate": "📊 正在生成综合评价…",
    "chat": "💬 正在组织回复…",
}


class WineCoachGraph:

    def __init__(self, checkpointer):
        self.memory = checkpointer
        self.agent = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(CoachState)

        graph.add_node("manager", manager_node)
        graph.add_node("profile", profile_node)
        graph.add_node("intent", intent_node)
        graph.add_node("question", question_node)
        graph.add_node("answer", answer_node)
        graph.add_node("evaluate", evaluate_node)
        graph.add_node("chat", chat_node)

        # 星型拓扑：所有节点都连回 manager，manager 统一调度
        graph.add_edge(START, "manager")
        graph.add_edge("profile", "manager")
        graph.add_edge("intent", "manager")
        graph.add_edge("question", "manager")
        graph.add_edge("answer", "manager")
        graph.add_edge("evaluate", "manager")
        graph.add_edge("chat", "manager")

        return graph.compile(checkpointer=self.memory)

    async def chat_events(self, question: str, user_id: str, thread_id: str):
        """
        事件流式对话，产出结构化事件

        stream_mode=["messages", "custom", "updates"]:
          - "custom"：节点内 get_stream_writer() 写出的逐 token 文本
          - "messages"：节点返回的完整 AIMessage
          - "updates"：节点执行完的返回值（状态提示 + 图表数据）
        """
        user_msg = {
            "messages": [HumanMessage(content=question)],
            "user_id": user_id,
            "session_id": thread_id,
        }
        config = {
            "configurable": {"thread_id": thread_id},
            # "recursion_limit": 50,
        }

        async for mode, data in self.agent.astream(
            user_msg, config, stream_mode=["messages", "custom", "updates"]
        ):
            if mode == "custom":
                if isinstance(data, str) and data:
                    yield {"kind": "token", "text": data}
            elif mode == "messages":
                chunk, meta = data
                content = getattr(chunk, "content", "")
                if content:
                    yield {"kind": "token", "text": content}
            elif mode == "updates":
                for node_name, update in data.items():
                    if node_name in NODE_STATUS:
                        yield {"kind": "status", "text": NODE_STATUS[node_name]}
                    if node_name == "evaluate" and isinstance(update, dict):
                        detail = update.get("evaluation_detail")
                        if detail:
                            yield {"kind": "chart", "data": detail}
