from fastapi import FastAPI
from app.web.chat_router.chat_router import chat_router
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()
#注册路由
app.include_router(chat_router)
#配置静态资源访问目录
app.mount("/static",StaticFiles(directory="./html"),name="static")

if __name__ =="__main__":
    uvicorn.run(app,host="localhost",port=8000)