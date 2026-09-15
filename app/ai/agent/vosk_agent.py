from vosk import Model, KaldiRecognizer  # Vosk语音识别核心库
import pyaudio                           # 音频输入输出库
import json                              # 处理JSON格式的识别结果

from fastapi import WebSocket

from app.ai.model.my_model import MyModel
class VoskAgent:
    _vosk =None
    def __init__(self):
        self.model = MyModel.get_vosk_model()
        self.stream = self.get_stream()
        self.re = KaldiRecognizer(self.model, 16000)
        #是否正在说话
        self.listing =False
    #定义静态函数
    @staticmethod
    def get_vosk():
        if VoskAgent._vosk is None:
            VoskAgent._vosk = VoskAgent()
            return  VoskAgent._vosk
        return VoskAgent._vosk
    def get_stream(self):
        # ------------加载本地音频配置--------------
        p = pyaudio.PyAudio()  # 创建PyAudio实例管理音频设备

        self.stream = p.open(
            format=pyaudio.paInt16,  # 16位整数格式
            channels=1,  # 单声道
            rate=16000,  # 16kHz采样率
            input=True,  # 输入模式（录音）
            frames_per_buffer=4096  # 每个缓冲区4096帧
        )
        return self.stream
    #开始说话业务
    async def speak(self,ws:WebSocket):
        await self.send_msg("开始说话",ws)
        #开启语音
        self.listing =True
        #开启音频
        self.stream.start_stream()
        while self.listing:
            data = self.re.AcceptWaveform(self.stream.read(4096))
            if data:
                rs = json.loads(self.re.Result())
                if rs["text"]:
                    await self.send_msg(rs["text"],ws)
    # 信息推送和语音的关闭
    async def send_msg(self,text,ws:WebSocket):
        if "开始说话" in text:
            await ws.send_text(text)
            return
        else:
            await ws.send_text(text)
            # 停止语音
            self.listing = False










