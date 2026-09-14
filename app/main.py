from fastapi import FastAPI
from app.web.chat_router.chat_router import chat_router
import uvicorn

app = FastAPI()
#注册路由
app.include_router(chat_router)

if __name__ =="__main__":
    uvicorn.run(app,host="localhost",port=8000)