"""
练习聊天接口：SSE 事件流 + 语音 WebSocket
对齐 wine_max：fetch 流式 + Authorization Bearer header 鉴权（JWT）
"""
import json
from fastapi import APIRouter, WebSocket, Depends, Query
from fastapi.responses import StreamingResponse
from common.jwt_decode import get_current_user, verify_token_or_none
from chat.service.chat_service import stream_chat
from common.app_context import AppContext
from ai.agent.vosk_agent import VoskAgent

chat_router = APIRouter()


@chat_router.get("/stream")
async def coach_stream(
    question: str = Query(..., description="用户问题"),
    session_id: str = Query(..., description="会话ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    SSE 事件流式练习接口（注册后为 /chat/stream）

    鉴权：从 Authorization: Bearer <token> 解出 user_id，不信任前端传参。

    返回格式（每条一行，SSE 规范）：
        data: {"kind": "status", "text": "..."}\n\n   后台状态提示
        data: {"kind": "token",  "text": "..."}\n\n   回答文本片段
        data: {"kind": "done"}\n\n                    结束标记
    """
    user_id = current_user["user_id"]
    coach_agent = AppContext.coach_agent

    async def generate():
        try:
            async for event in stream_chat(question, user_id, session_id, coach_agent):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            detail = str(e).strip() or type(e).__name__
            yield f"data: {json.dumps({'kind': 'error', 'text': f'流式异常: {detail}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@chat_router.get("/status")
async def vosk_status():
    """查询语音模型是否已加载（前端语音按钮就绪轮询用）"""
    return {"loaded": AppContext.is_vosk_ready()}


@chat_router.get("/session_state")
async def session_state(
    session_id: str = Query(..., description="会话ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    查询指定会话的练习状态（断点续传/进度展示用）。
    从 checkpointer 读出 practice_step / current_index 等给前端展示进度，无状态则返回 null。
    """
    state = await AppContext.get_session_state(session_id)
    if state is None:
        return {"code": 200, "msg": "ok", "data": None}
    # 鉴权：只能查自己的会话
    if str(state["user_id"]) != str(current_user["user_id"]):
        return {"code": 403, "msg": "无权访问该会话", "data": None}
    return {"code": 200, "msg": "ok", "data": state}


@chat_router.websocket("/vosk")
async def vosk_ws(ws: WebSocket, token: str):
    """
    语音识别 WebSocket（注册后为 /chat/vosk?token=...）

    协议：
    - 前端发送二进制音频数据（16k 单声道 PCM）
    - 后端返回：{"status": "listening/partial/final", "text": "识别文本"}
    - 前端发送字符串 "stop" 时结束识别
    """
    # ========== 功能模块：JWT 认证（WebSocket 无法走 Depends，手动验证） ==========
    user = verify_token_or_none(token)
    if not user:
        await ws.close(code=4001, reason="认证失败")
        return

    # ========== 功能模块：检查 Vosk 是否就绪 ==========
    if not AppContext.is_vosk_ready():
        await ws.send_text(json.dumps({
            "status": "error",
            "text": "语音模型加载中，请稍候"
        }, ensure_ascii=False))
        await ws.close()
        return

    try:
        await ws.accept()
        vosk_agent = VoskAgent.get_vosk()
        await vosk_agent.recognize_stream(ws)
    except Exception as e:
        print(f"Vosk WebSocket 异常: {e}")
        await ws.close()
