from fastapi import APIRouter

chat_router = APIRouter()

#聊天接口
@chat_router.get("/chat")
async def chat(question:str,user_id:str):
    print(f"用户问题:{question},用户ID:{user_id}")
    #模拟AI回复
    ai_msg = "你好，我是多智能体AI面试助手"
    #返回结果是json
    return {"code":200,"data":ai_msg}






