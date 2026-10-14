"""
应用上下文：启动时预加载所有重资源（图 / checkpointer / 语音模型）
用 AsyncPostgresSaver 做 checkpointer 持久化图状态
（图用 astream 异步流，需异步版 checkpointer）
"""
from typing import Any
import os

from ai.model.my_model import MyModel
from ai.agent.multi_agent.graph.coach_graph import WineCoachGraph


class AppContext:
    coach_agent: WineCoachGraph | None = None
    _vosk_loaded: bool = False
    _memory: Any = None  # 持有 checkpointer 引用，避免被垃圾回收

    @classmethod
    async def _build_checkpointer(cls) -> Any:
        """
        构建 LangGraph checkpointer。

        优先 AsyncPostgresSaver（图状态持久化到 PostgreSQL，复用连接池）；
        连接失败则降级 InMemorySaver（服务仍可启动，仅状态不持久化）。
        """
        postgres_url = os.getenv("POSTGRES_URL", "")
        if postgres_url:
            try:
                from langgraph.checkpoint.postgres import aio
                from common import pg_util
                pool = pg_util.init_pool(postgres_url)
                await pg_util.open_pool()
                saver = aio.AsyncPostgresSaver(conn=pool)
                await saver.setup()  # 首次运行自动创建 checkpoint 表
                print("[AppContext] AsyncPostgresSaver 加载完成（图状态持久化）")
                return saver
            except Exception as e:
                print(f"[AppContext] AsyncPostgresSaver 连接失败，降级 InMemorySaver: {e}")

        from langgraph.checkpoint.memory import InMemorySaver
        print("[AppContext] 使用 InMemorySaver（图状态不持久化）")
        return InMemorySaver()

    @classmethod
    async def init(cls) -> None:
        """预加载所有重资源"""
        # 1. LangGraph 练习智能体（checkpointer 持久化 thread 状态）
        memory = await cls._build_checkpointer()
        cls._memory = memory
        cls.coach_agent = WineCoachGraph(memory)
        print("[AppContext] WineCoach 智能体加载完成")

        # 2. Vosk 语音模型（可选，路径存在才加载）
        vosk_path = os.getenv("VOSK_PATH")
        if vosk_path and os.path.exists(vosk_path):
            try:
                MyModel.get_vosk_model()
                cls._vosk_loaded = True
                print("[AppContext] Vosk 语音模型加载完成")
            except Exception as e:
                print(f"[AppContext] Vosk 加载失败: {e}")
        else:
            print("[AppContext] Vosk 模型路径未配置，跳过语音功能")

    @classmethod
    def is_vosk_ready(cls) -> bool:
        return cls._vosk_loaded

    @classmethod
    async def get_session_state(cls, thread_id: str) -> dict | None:
        """
        从 checkpointer 读取指定会话的状态（断点续传用）。
        返回 state 字典，或 None（不存在/无 checkpointer）。
        """
        if cls._memory is None:
            return None
        try:
            ckpt = await cls._memory.aget({"configurable": {"thread_id": thread_id}})
            if ckpt is None:
                return None
            state = ckpt.get("channel_values", {})
            # checkpoint 里真正的图状态存在 channel_values 这个键下
            # channel_values 是 LangGraph 框架内部定义的，是 checkpoint 对象里的一个固定键（key）。
            useful = {}
            for key in [
                "practice_step", "question_count", "current_index",
                "question_type", "sales_stage", "customer_type", "product_category",
                "country", "questions", "user_answer_list", "question_id",
                "continue_question", "evaluation", "evaluation_detail",
                "user_id", "session_id",
                "profile", "keywords",
            ]:
                if key in state:
                    useful[key] = state[key]
            return useful
        except Exception as e:
            print(f"[AppContext] get_session_state 失败: {e}")
            return None
