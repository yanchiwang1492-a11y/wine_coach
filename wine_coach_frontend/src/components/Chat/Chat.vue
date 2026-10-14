<template>
  <div id="app" class="app-container">
    <ChatSidebar
      v-model:searchKeyword="searchKeyword"
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :sidebar-open="sidebarOpen"
      @close-sidebar="sidebarOpen = false"
      @create-session="createNewSession"
      @switch-session="switchSession"
      @delete-session="deleteSession"
    />

    <div class="main-panel">
      <ChatHeader
        :user-name="userName"
        :chat-title="chatTitle"
        @logout="logout"
        @go-home="$router.push('/')"
        @back-to-select="backToSelect"
        @toggle-sidebar="sidebarOpen = !sidebarOpen"
      />

      <!-- 常驻顶部：进度条 + 画像 chip -->
      <div class="top-bar">
        <div class="top-bar-left">
          <span class="progress-icon">📊</span>
          <span class="progress-text">{{ progressText }}</span>
        </div>
        <div class="top-bar-right">
          <span
            class="profile-chip"
            :class="{ expanded: profileExpanded }"
            @click="profileExpanded = !profileExpanded"
          >
            <span class="chip-icon">🏆</span>
            <span class="chip-text">销冠画像</span>
            <span v-if="profileExpanded" class="profile-detail">
              <span v-for="tag in profileTags" :key="tag.label" class="profile-tag">{{ tag.label }}：{{ tag.value }}</span>
            </span>
          </span>
        </div>
      </div>

      <ChatMessageList
        ref="chatListComp"
        v-model:email-input="emailInput"
        :chat-list="chatList"
        :status-text="statusText"
        :dimensions="dimensions"
        :is-sending="isSending"
        @random-by-dimension="randomByDimension"
        @random-by-option="randomByOption"
        @view-answer="viewAnswer"
        @change-question="changeQuestion"
        @send-email="sendEmailReport"
      />

      <ChatInput
        ref="chatInput"
        v-model:input-text="inputText"
        :is-sending="isSending"
        :is-recording="isRecording"
        :vosk-ready="voskReady"
        @send-message="sendMessage"
        @toggle-voice="toggleVoice"
        @enter-key="sendMessage"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import ChatSidebar from './ChatSidebar.vue'
import ChatHeader from './ChatHeader.vue'
import ChatMessageList from './ChatMessageList.vue'
import ChatInput from './ChatInput.vue'
import { streamChat, getSessionProgress } from '../../api/chat'
import { clearAuth } from '../../utils/auth'

const router = useRouter()

// ========== 数据 ==========
const userName = ref(sessionStorage.getItem('user_name') || '')
const chatTitle = 'WineCoach丨葡萄酒销售实战模拟平台'
const sessions = ref([])
const currentSessionId = ref(null)
const chatList = ref([])
const searchKeyword = ref('')
const sidebarOpen = ref(false)

const inputText = ref('')
const isSending = ref(false)
const abortController = ref(null)

// 语音相关（WebSocket + AudioContext 复杂逻辑留在主组件，经 props/emit 与 ChatInput 交互）
const isRecording = ref(false)
const voskReady = ref(false)
const ws = ref(null)
const audioContext = ref(null)
const mediaStream = ref(null)
const scriptProcessor = ref(null)
const sourceNode = ref(null)

const statusText = ref('')   // 后台状态提示（"正在干嘛"，事件流 status 事件写入）
const sessionProgress = ref(null)  // 会话练习进度（断点续传用，从 checkpointer 读取）
const emailInput = ref(sessionStorage.getItem('email') || '')   // 邮件发送输入框（预填注册/登录时的邮箱）

// 画像相关
const profileExpanded = ref(false)

// 销冠画像标签：与题库维度对齐，无值默认「不限」
const CHAMPION_LABELS = [
  { key: 'product_focus', label: '主营国家', fallback: '不限' },   // 对应题库「国家」维度
  { key: 'sales_channel', label: '销售渠道', fallback: '不限' },
  { key: 'customer_group', label: '主要客户', fallback: '不限' },   // 对应题库「客户画像」维度
  { key: 'goal', label: '提升目标', fallback: '不限' },   // 对应题型/阶段
  { key: 'company_type', label: '公司类型', fallback: '不限' },
]

// 销冠画像标签列表（无值补「不限」，保证 5 个标签常驻展示）
const profileTags = computed(() => {
  const p = sessionProgress.value?.profile || {}
  return CHAMPION_LABELS.map(item => ({
    label: item.label,
    value: p[item.key] || item.fallback,
  }))
})

// 进度文案（常驻显示，无时显示"等待开始"）
const progressText = computed(() => {
  const p = sessionProgress.value
  if (!p || !p.question_count || p.question_count <= 0) {
    const step = p?.practice_step
    if (step === 'start') return '准备开始练习'
    return '等待开始练习'
  }
  const cur = p.current_index || 0
  const total = p.question_count
  const step = p.practice_step === 'done' ? '已完成 ✓' : `第 ${cur} / ${total} 题`
  return step
})

const chatListComp = ref(null)
const chatInput = ref(null)

// 维度卡片定义（与后端题库 5 维度对齐）
const dimensions = [
  { key: 'question_type', title: '考什么（类型）', options: ['知识', '话术', '情景应对', '产品推荐'] },
  { key: 'sales_stage', title: '哪个环节（销售阶段）', options: ['迎宾', '需求挖掘', '推荐', '异议处理', '成交', '售后'] },
  { key: 'customer_type', title: '哪类客户（客户画像）', options: ['新手', '送礼', '宴请', '收藏', '团购'] },
  { key: 'product_category', title: '涉哪个品类（产品知识）', options: ['产区', '品种', '年份', '配餐', '储存'] },
  { key: 'country', title: '哪个国家（产区）', options: ['法国', '意大利', '西班牙', '德国', '葡萄牙', '美国', '智利', '阿根廷', '澳大利亚', '新西兰', '南非', '中国', '奥地利', '希腊', '格鲁吉亚', '匈牙利', '罗马尼亚', '摩尔多瓦', '乌拉圭', '巴西'] },
]

// 维度 → 出题提示语映射（后端 intent_node 据此识别维度）
const PROMPT_MAP = {
  question_type: (opt) => `来1道${opt}题`,
  sales_stage: (opt) => `来1道${opt}阶段的题`,
  customer_type: (opt) => `来1道${opt}客户的题`,
  product_category: (opt) => `来1道关于${opt}的题`,
  country: (opt) => `来1道${opt}酒的题`,
}

// 点击维度卡片：从该维度随机抽一个分类出题
function randomByDimension(dimKey) {
  const dim = dimensions.find(d => d.key === dimKey)
  const opt = dim.options[Math.floor(Math.random() * dim.options.length)]
  sendByPrompt(PROMPT_MAP[dimKey](opt))
}

// 点击具体标签：从该分类精准出题
function randomByOption(dimKey, opt) {
  sendByPrompt(PROMPT_MAP[dimKey](opt))
}

function sendByPrompt(prompt) {
  inputText.value = prompt
  nextTick(() => sendMessage())
}

// 查看当前题目参考答案（文案统一为"查看答案"）
function viewAnswer() {
  inputText.value = '查看答案'
  nextTick(() => sendMessage())
}

// 换一题：发"换一题"信号，后端移除当前题重新出同维度新题
function changeQuestion() {
  inputText.value = '换一题'
  nextTick(() => sendMessage())
}

// ========== 会话管理 ==========
function loadSessions() {
  return axios.get('/history/')
    .then(res => {
      sessions.value = res.data.data || []
    })
    .catch(() => {
      ElMessage.error('加载会话失败')
    })
}

function switchSession(sessionId) {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  isSending.value = false
  currentSessionId.value = sessionId
  sidebarOpen.value = false

  // 加载历史消息
  axios.get(`/history/${sessionId}`)
    .then(res => {
      const data = res.data.data || {}
      chatList.value = (data.messages || []).map(m => ({
        role: m.role,
        content: m.content,
        isStreaming: false
      }))
      nextTick(() => scrollToBottom())
    })
    .catch(() => {
      ElMessage.error('加载会话详情失败')
      chatList.value = []
    })

  // 加载练习进度（断点续传）
  getSessionProgress(sessionId)
    .then(state => {
      sessionProgress.value = state
    })
    .catch(() => {
      sessionProgress.value = null
    })

  nextTick(() => {
    if (chatInput.value) chatInput.value.inputFocus()
  })
}

function createNewSession() {
  return axios.post('/history/new')
    .then(res => {
      const sid = res.data.data?.session_id
      if (sid) {
        currentSessionId.value = sid
        chatList.value = []
        sessionProgress.value = null
      }
      return sid
    })
    .catch(() => {
      ElMessage.error('新建会话失败')
      return null
    })
}

function deleteSession(sessionId) {
  if (!confirm('确定删除这个对话吗？')) return

  axios.delete(`/history/${sessionId}`)
    .then(() => {
      const wasCurrent = currentSessionId.value === sessionId
      loadSessions().then(() => {
        if (wasCurrent) {
          if (sessions.value.length > 0) {
            switchSession(sessions.value[0].session_id)
          } else {
            currentSessionId.value = null
            chatList.value = []
          }
        }
      })
    })
    .catch(() => {
      ElMessage.error('删除会话失败')
    })
}

// 返回选择：中断当前请求，新建会话回到空状态（维度卡片）
async function backToSelect() {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  isSending.value = false
  statusText.value = ''
  await createNewSession()
  await loadSessions()
}

// ========== 发送 ==========
async function sendMessage() {
  const question = inputText.value.trim()
  if (!question || isSending.value) return

  if (isRecording.value) {
    stopRecording(false)
  }

  // 确保有会话（无则新建）—— 放在 push 消息之前，避免 createNewSession 清空 chatList
  if (!currentSessionId.value) {
    const sid = await createNewSession()
    if (!sid) {
      isSending.value = false
      return
    }
    await loadSessions()
  }

  isSending.value = true
  statusText.value = '🚀 已收到，开始处理…'
  chatList.value.push({ role: 'user', content: question })
  inputText.value = ''

  const aiMsg = { role: 'assistant', content: '', isStreaming: true, chart: null }
  chatList.value.push(aiMsg)
  const aiMsgIdx = chatList.value.length - 1
  scrollToBottom()

  abortController.value = new AbortController()

  try {
    await streamChat({
      question,
      sessionId: currentSessionId.value,
      signal: abortController.value.signal,
      onStatus: (text) => { statusText.value = text },
      onToken: (text) => {
        aiMsg.content += text
        scrollToBottom()
      },
      onChart: (data) => { aiMsg.chart = data },
      onError: (text) => { aiMsg.content += text }
    })

    aiMsg.isStreaming = false
    isSending.value = false
    statusText.value = ''
    abortController.value = null
    if (aiMsg.chart && aiMsg.chart.length) chatListComp.value.renderCharts(aiMsgIdx)
    loadSessions()
    // 每轮对话结束刷新进度（断点续传进度条）
    getSessionProgress(currentSessionId.value).then(s => { sessionProgress.value = s }).catch(() => {})
  } catch (err) {
    aiMsg.isStreaming = false
    isSending.value = false
    statusText.value = ''
    abortController.value = null
    if (err.name === 'AbortError') return  // 用户主动中断：静默重置，不弹错
    if (!aiMsg.content) {
      aiMsg.content = '连接异常，请稍后重试。'
    }
    ElMessage.error('发送失败')
  }
}

function scrollToBottom() {
  chatListComp.value?.scrollToBottom()
}

function sendEmailReport() {
  const email = emailInput.value.trim()
  if (!email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  inputText.value = `请把评估报告发送到邮箱 ${email}`
  nextTick(() => sendMessage())
}

// ========== 登出 ==========
function logout() {
  axios.post('/users/logout').finally(() => {
    clearAuth()
    router.push('/login')
  })
}

// ========== 语音 ==========
function checkVoskStatus() {
  const check = () => {
    axios.get('/chat/status')
      .then(res => {
        if (res.data.loaded) {
          voskReady.value = true
        } else {
          setTimeout(check, 1000)
        }
      })
      .catch(() => {
        setTimeout(check, 2000)
      })
  }
  check()
}

function toggleVoice() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startRecording() {
  if (!voskReady.value) {
    alert('语音模型正在加载，请稍候…')
    return
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('当前浏览器不支持语音录制功能')
    return
  }

  const constraints = {
    audio: {
      channelCount: 1,
      sampleRate: 48000,
      echoCancellation: true,
      noiseSuppression: true,
    }
  }

  navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => {
      mediaStream.value = stream
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      audioContext.value = new AudioCtx({ sampleRate: 48000 })

      sourceNode.value = audioContext.value.createMediaStreamSource(stream)
      scriptProcessor.value = audioContext.value.createScriptProcessor(4096, 1, 1)

      const inputRate = audioContext.value.sampleRate
      const targetRate = 16000

      scriptProcessor.value.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0)
        const pcm16 = downsampleTo16kPCM(inputData, inputRate, targetRate)
        if (ws.value && ws.value.readyState === WebSocket.OPEN) {
          ws.value.send(pcm16)
        }
      }

      sourceNode.value.connect(scriptProcessor.value)
      scriptProcessor.value.connect(audioContext.value.destination)

      connectVoskWS()
      isRecording.value = true
    })
    .catch(err => {
      console.error('麦克风权限失败:', err)
      alert('无法访问麦克风，请检查浏览器权限设置')
    })
}

function stopRecording(waitFinal = true) {
  // waitFinal=true：发送 stop 等待后端返回最终文本（用于"停止录音"按钮）
  // waitFinal=false：直接断开、忽略最终文本（用于发送/出错，避免 final 异步写回输入框）
  if (ws.value) {
    if (waitFinal && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send('stop')
    } else {
      ws.value.close()
      ws.value = null
    }
  }

  if (scriptProcessor.value) {
    scriptProcessor.value.disconnect()
    scriptProcessor.value = null
  }
  if (sourceNode.value) {
    sourceNode.value.disconnect()
    sourceNode.value = null
  }
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }
  if (audioContext.value) {
    audioContext.value.close()
    audioContext.value = null
  }

  isRecording.value = false
  // 停止录音后不自动发送，文字留在输入框，由用户点发送按钮发送
}

function connectVoskWS() {
  const token = sessionStorage.getItem('token') || ''
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
  const wsUrl = `${scheme}://${location.host}/chat/vosk?token=${token}`
  // location.host 是 hostname 和 port 拼起来的：localhost:8080
  // 拼出来是 ws://localhost:8080/chat/vosk?token=xxx
  ws.value = new WebSocket(wsUrl)
  ws.value.binaryType = 'arraybuffer'

  ws.value.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.status === 'listening') {
        // 后端就绪
      } else if (data.status === 'final') {
        if (data.text && data.text.trim()) {
          inputText.value = data.text.replace(/\s+/g, '')
        }
        ws.value.close()
      } else if (data.status === 'partial') {
        if (data.text) {
          inputText.value = data.text.replace(/\s+/g, '')
        }
      }
    } catch (err) {
      console.error('语音消息解析失败:', err)
    }
  }

  ws.value.onerror = (err) => {
    console.error('语音 WebSocket 错误:', err)
    ws.value = null
    if (isRecording.value) {
      stopRecording(false)
    }
  }

  ws.value.onclose = () => {
    ws.value = null
  }
}

function downsampleTo16kPCM(input, inputRate, outputRate) {
  if (inputRate === outputRate) {
    return floatTo16BitPCM(input)
  }
  const ratio = inputRate / outputRate
  const newLen = Math.floor(input.length / ratio)
  const output = new Float32Array(newLen)
  let offset = 0
  for (let i = 0; i < newLen; i++) {
    const next = Math.floor((i + 1) * ratio)
    let sum = 0, count = 0
    for (let j = offset; j < next && j < input.length; j++) {
      sum += input[j]
      count++
    }
    output[i] = count > 0 ? sum / count : 0
    offset = next
  }
  return floatTo16BitPCM(output)
}

function floatTo16BitPCM(input) {
  const buffer = new ArrayBuffer(input.length * 2)
  const view = new DataView(buffer)
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]))
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
  return buffer
}

// ========== 生命周期 ==========
onMounted(async () => {
  await loadSessions()
  checkVoskStatus()
  nextTick(() => {
    if (chatInput.value) chatInput.value.inputFocus()
  })
})

onBeforeUnmount(() => {
  if (abortController.value) abortController.value.abort()
  if (ws.value) ws.value.close()
  if (isRecording.value) stopRecording()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  overflow: hidden;
}

.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  position: relative;
}

/* 常驻顶部栏 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 24px;
  background: #fff7ed;
  border-bottom: 1px solid #fed7aa;
  font-size: 0.85rem;
  color: #c2410c;
  flex-shrink: 0;
}
.top-bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}
.progress-icon {
  font-size: 1rem;
}
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.profile-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #ffffff;
  border: 1px solid #fed7aa;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.15s;
  max-width: 200px;
  overflow: hidden;
}
.profile-chip:hover {
  background: #ffedd5;
  border-color: #fb8600;
}
.chip-icon {
  font-size: 0.9rem;
}
.chip-text {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.profile-chip.expanded {
  max-width: none;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 14px;
  position: absolute;
  right: 24px;
  top: 42px;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(251, 134, 0, 0.15);
  min-width: 200px;
}
.profile-chip.expanded .chip-text {
  display: none;
}
.profile-detail {
  display: none;
}
.profile-chip.expanded .profile-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}
.profile-tag {
  font-size: 0.8rem;
  color: #7c2d12;
  line-height: 1.4;
}
</style>