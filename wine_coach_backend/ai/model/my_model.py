"""
基于单例模式的模型封装
"""
from langchain_openai import ChatOpenAI
import os
from vosk import Model

# LLM 调用超时（秒）：本地模型较慢，给足时间避免误判超时
LLM_TIMEOUT = 300


class MyModel:
    _model = None           # 线上模型
    _local_model = None     # 本地模型
    _vosk_model = None      # 语音识别模型

    @staticmethod
    def _build_chat_model(model_name: str, api_key: str, base_url: str) -> ChatOpenAI:
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            streaming=True,
            temperature=0.7,
            extra_body={"enable_thinking": False},
        )

    @staticmethod
    def get_online_model() -> ChatOpenAI:
        """获取线上大模型（意图识别、评价等高准确率场景）"""
        if MyModel._model is None:
            MyModel._model = MyModel._build_chat_model(
                os.getenv("MODEL_ONLINE_NAME"),
                os.getenv("DASHSCOPE_API_KEY"),
                os.getenv("MODEL_BASE_URL"),
            )
        return MyModel._model

    @staticmethod
    def get_local_model() -> ChatOpenAI:
        """获取本地大模型（轻量/离线场景）"""
        if MyModel._local_model is None:
            MyModel._local_model = MyModel._build_chat_model(
                os.getenv("MODEL_LOCAL_NAME"),
                "empty",
                os.getenv("LOCAL_URL"),
            )
        return MyModel._local_model

    @staticmethod
    def get_vosk_model() -> Model:
        """获取 Vosk 语音识别模型"""
        if MyModel._vosk_model is None:
            model_path = os.getenv("VOSK_PATH")
            MyModel._vosk_model = Model(model_path=model_path)
        return MyModel._vosk_model


if __name__ == "__main__":
    """模型自测：python ai/model/my_model.py"""
    import asyncio
    import time

    from dotenv import load_dotenv

    load_dotenv()

    # 1. 单例校验
    local1, local2 = MyModel.get_local_model(), MyModel.get_local_model()
    online1, online2 = MyModel.get_online_model(), MyModel.get_online_model()
    print(f"本地模型单例: {'通过' if local1 is local2 else '失败'}")
    print(f"线上模型单例: {'通过' if online1 is online2 else '失败'}")
    print(f"本地模型: model={os.getenv('MODEL_LOCAL_NAME')} url={os.getenv('LOCAL_URL')}")
    print(f"线上模型: model={os.getenv('MODEL_ONLINE_NAME')} url={os.getenv('MODEL_BASE_URL')}")

    # 2. 本地模型连通性/耗时测试（需 Ollama 运行）
    async def _test_local() -> None:
        start = time.perf_counter()
        resp = await asyncio.wait_for(
            MyModel.get_local_model().ainvoke("请回复两个字：收到"),
            timeout=LLM_TIMEOUT,
        )
        elapsed = time.perf_counter() - start
        print(f"本地模型响应: {resp.content} (耗时 {elapsed:.1f}s)")

    try:
        asyncio.run(_test_local())
    except Exception as e:
        print(f"本地模型测试失败: {e}")
