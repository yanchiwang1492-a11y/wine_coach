from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from app.test.test_agent import test_agent
chat_router = APIRouter()


#聊天接口
@chat_router.get("/chat")
async def chat(question:str,user_id:str):
    print(f"用户问题:{question},用户ID:{user_id}")

        # 定义一个异步迭代七
    async def generate(question, user_id):
        try:

            async for x in test_agent(question):

                # False 流式未结束
                data = {"data": x, "done": False}
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            # 流式结束
            data = {"data": "", "done": True}
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        except Exception as e:
            # 流式结束
            data = {"data": "流式异常", "done": True}
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(question,user_id),media_type="text/event-stream")






