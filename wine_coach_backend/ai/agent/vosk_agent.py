"""
Vosk 语音识别 Agent：接收前端 WebSocket 上传的音频流，在服务端做识别。
"""
import json

from fastapi import WebSocket
from vosk import KaldiRecognizer

from ai.model.my_model import MyModel


class VoskAgent:
    _instance = None

    def __init__(self):
        self.model = MyModel.get_vosk_model()

    @staticmethod
    def get_vosk() -> "VoskAgent":
        """单例获取 VoskAgent"""
        if VoskAgent._instance is None:
            VoskAgent._instance = VoskAgent()
        return VoskAgent._instance

    async def recognize_stream(self, ws: WebSocket):
        """
        从 WebSocket 接收音频流，实时识别文本并推送。

        协议：
        - 前端发送二进制音频数据（16k 单声道 PCM，小端 16bit）
        - 后端识别到完整句子后推送 JSON：{"text": "识别结果"}
        - 前端发送字符串 "stop" 时结束识别
        """
        recognizer = KaldiRecognizer(self.model, 16000)
        recognizer.SetWords(False)

        # 通知前端开始接收音频
        await ws.send_text(json.dumps({"status": "listening", "text": ""}, ensure_ascii=False))

        while True:
            try:
                # 接收数据：二进制为音频，文本为控制命令
                data = await ws.receive()
                if data["type"] == "websocket.disconnect":
                    break

                if "bytes" in data:
                    audio_bytes = data["bytes"]
                    if recognizer.AcceptWaveform(audio_bytes):
                        result = json.loads(recognizer.Result())
                        if result.get("text"):
                            await ws.send_text(
                                json.dumps({"status": "partial", "text": result["text"]}, ensure_ascii=False)
                            )
                    else:
                        partial = json.loads(recognizer.PartialResult())
                        if partial.get("partial"):
                            # 实时推送中间识别结果，前端即时刷新输入框
                            await ws.send_text(
                                json.dumps({"status": "partial", "text": partial["partial"]}, ensure_ascii=False)
                            )
                elif "text" in data:
                    text = data["text"]
                    if text == "stop":
                        # 结束识别，输出最终结果
                        final_result = json.loads(recognizer.FinalResult())
                        final_text = final_result.get("text", "")
                        await ws.send_text(
                            json.dumps({"status": "final", "text": final_text}, ensure_ascii=False)
                        )
                        break
            except Exception as e:
                print(f"语音识别流异常: {e}")
                break

        await ws.close()
