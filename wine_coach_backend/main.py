"""
WineCoach 后端服务入口
"""
import sys
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()  # 最早加载环境变量，后续模块依赖

from common.console_util import ensure_utf8_console

ensure_utf8_console()

# Windows 上 psycopg async 需要 SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Windows 上 psycopg 的异步模式不兼容默认的事件循环，必须换成 SelectorEventLoop 才能跑。
# Python 在 Windows 上默认用的是 ProactorEventLoop

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from chat.controller.chat_controller import chat_router
from chat.controller.history_controller import history_router
from users.controller.users_controller import users_router
from common.app_context import AppContext


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 如果你不需要访问 app，删掉app: FastAPI完全没问题
    print("服务器启动")
    await AppContext.init()
    print("预加载完成")
    yield
    print("服务器关闭")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/users", tags=["用户"])
app.include_router(chat_router, prefix="/chat", tags=["聊天"])
app.include_router(history_router, prefix="/history", tags=["历史"])


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.getenv("PORT"))
    uvicorn.run('main:app', host=host, port=port, reload=True)
    # os.getenv() 读出来永远是字符串
    # reload=True = 热重载（自动重启）：你改代码保存后，服务器自动重启，不用手动停掉再开。
