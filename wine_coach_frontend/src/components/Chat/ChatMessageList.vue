<template>
  <div class="chat-container" ref="chatContainer">
    <!-- 空状态 -->
    <div class="empty-state" v-if="chatList.length === 0 && !isSending">
      <div class="empty-brand">智能随机出题系统</div>
      <div class="empty-desc">点击下方任意考核维度随机抽题，或点击标签精准抽题</div>

      <!-- 维度卡片：点击卡片随机抽该维度，点击标签精准抽题 -->
      <div class="dimension-list">
        <div v-for="dim in dimensions" :key="dim.key" class="dimension-card">
          <div class="dimension-header" @click="$emit('randomByDimension', dim.key)">
            <span class="dimension-title">{{ dim.title }}</span>
            <span class="dimension-hint">🎲 随机抽题</span>
          </div>
          <div class="dimension-tags">
            <span
              v-for="opt in dim.options"
              :key="opt"
              class="dimension-tag"
              @click="$emit('randomByOption', dim.key, opt)"
            >
              {{ opt }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-scroll" v-show="chatList.length > 0">
      <template v-for="(msg, idx) in chatList" :key="idx">
        <div class="message" :class="msg.role">
          <div class="msg-content">
            <div class="msg-role-label" v-if="msg.role === 'assistant'">WineCoach</div>
            <!-- 状态条：流式时显示"后台正在干嘛" -->
            <div v-if="msg.role === 'assistant' && msg.isStreaming && statusText" class="status-line">
              <span class="status-dot"></span>{{ statusText }}
            </div>
            <div v-if="msg.role === 'assistant'" class="bot-md" v-html="formatMessage(msg.content)"></div>
            <template v-else>{{ msg.content }}</template>
            <span v-if="msg.role === 'assistant' && msg.isStreaming" class="typing-cursor"></span>

            <!-- 出题消息附轻量内联操作按钮 -->
            <div v-if="isQuestionMessage(msg) && !msg.isStreaming" class="question-actions">
              <button class="qa-btn" @click="$emit('viewAnswer')">查看答案</button>
              <button class="qa-btn" @click="$emit('changeQuestion')">换一题</button>
            </div>
          </div>
        </div>

        <!-- 该消息的评估图表（固定在评估消息下方，不随新消息漂移） -->
        <div v-if="msg.chart && msg.chart.length" class="chart-card">
          <div class="chart-title">📊 练习得分可视化</div>
          <div class="chart-box" :data-radar="idx"></div>
          <div class="chart-box" :data-bar="idx"></div>
          <div class="email-send">
            <el-input
              :model-value="emailInput"
              @update:model-value="$emit('update:emailInput', $event)"
              placeholder="输入邮箱，把评估报告发送到邮箱"
              clearable
            />
            <el-button class="email-btn" @click="$emit('sendEmail')">发送报告</el-button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { formatMessage } from '../../utils/markdown'

const props = defineProps({
  chatList: { type: Array, default: () => [] },
  statusText: { type: String, default: '' },
  sessionProgress: { type: Object, default: null },
  dimensions: { type: Array, default: () => [] },
  isSending: { type: Boolean, default: false },
  emailInput: { type: String, default: '' },
})

defineEmits([
  'randomByDimension',
  'randomByOption',
  'viewAnswer',
  'changeQuestion',
  'sendEmail',
  'update:emailInput',
])

const chatContainer = ref(null)

// 判断是否为出题消息（含"第N题:"冒号格式，且非评价报告）
function isQuestionMessage(msg) {
  if (msg.role !== 'assistant') return false
  // 出题消息格式为"第N题:题目"（半角/全角冒号紧跟），聊天回复里出现"第N题"但无冒号则不误判
  if (!/第\s*\d+\s*题[:：]/.test(msg.content || '')) return false
  // 排除评价报告（含"综合评价/训练建议/整体评价"特征，不显示查看答案/换一题）
  if (/综合评价|训练建议|整体评价/.test(msg.content || '')) return false
  return true
}

// 滚动到底部（父组件在 token 到达/切换会话时调用）
function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// ========== echarts 图表 ==========
// 评估完成后，在对应消息下方渲染雷达图 + 柱状图（图表绑定到消息，不随新消息漂移）
function renderCharts(msgIdx) {
  nextTick(() => {
    const radarEl = document.querySelector(`[data-radar="${msgIdx}"]`)
    const barEl = document.querySelector(`[data-bar="${msgIdx}"]`)
    const scores = props.chatList[msgIdx]?.chart || []
    renderRadar(radarEl, scores)
    renderBar(barEl, scores)
  })
}

// 雷达图：三个维度（知识/技巧/表达）的平均得分，展示能力画像
function renderRadar(el, scores) {
  if (!el || !scores.length) return
  const chart = echarts.init(el)
  const avg = (key) => {
    const sum = scores.reduce((s, q) => s + (Number(q[key]) || 0), 0)
    return scores.length ? Number((sum / scores.length).toFixed(1)) : 0
  }
  chart.setOption({
    tooltip: {},
    radar: {
      indicator: [
        { name: '专业知识', max: 60 },
        { name: '销售技巧', max: 25 },
        { name: '表达沟通', max: 15 }
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: [avg('knowledge_score'), avg('skill_score'), avg('expression_score')],
        name: '能力画像'
      }]
    }]
  })
}

// 柱状图：逐题总分
function renderBar(el, scores) {
  if (!el || !scores.length) return
  const chart = echarts.init(el)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: scores.map((q, i) => `第${i + 1}题`) },
    yAxis: { type: 'value', max: 100 },
    series: [{
      type: 'bar',
      data: scores.map(q => Number(q.total_score) || 0),
      itemStyle: { color: '#fb8600' }
    }]
  })
}

defineExpose({ scrollToBottom, renderCharts })
</script>

<style scoped>
.chat-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.chat-scroll {
  flex: 1;
  padding: 28px 20px 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.empty-brand {
  font-size: 2.2rem;
  font-weight: 700;
  color: #fb8600;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 0.95rem;
  color: #6b7280;
  margin-bottom: 32px;
}

/* 维度卡片布局 */
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 560px;
  width: 100%;
  margin-bottom: 28px;
}

.dimension-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  overflow: hidden;
  transition: all 0.15s;
}

.dimension-card:hover {
  border-color: #fb8600;
  box-shadow: 0 2px 10px rgba(251, 134, 0, 0.08);
}

.dimension-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.dimension-header:hover {
  background: #fff7ed;
}

.dimension-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1f2937;
}

.dimension-hint {
  font-size: 0.75rem;
  color: #fb8600;
  font-weight: 500;
}

.dimension-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
}

.dimension-tag {
  padding: 5px 14px;
  font-size: 0.82rem;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  cursor: pointer;
  color: #374151;
  background: #ffffff;
  transition: all 0.15s;
}

.dimension-tag:hover {
  border-color: #fb8600;
  background: #fff7ed;
  color: #fb8600;
}

/* 出题消息轻量操作按钮 */
.question-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.qa-btn {
  padding: 4px 12px;
  font-size: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
}

.qa-btn:hover {
  border-color: #fb8600;
  color: #fb8600;
  background: #fff7ed;
}

/* 消息 */
.message {
  width: 100%;
  max-width: 768px;
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: fadeInUp 0.25s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  justify-content: flex-end;
}

.msg-content {
  max-width: 100%;
  line-height: 1.7;
  font-size: 0.95rem;
}

.message.user .msg-content {
  order: 1;
  background: #fb8600;
  color: #ffffff;
  padding: 12px 18px;
  border-radius: 18px;
  border-top-right-radius: 4px;
  word-break: break-word;
}

.message.assistant .msg-content {
  color: #1f2937;
  padding-top: 4px;
}

.msg-role-label {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-bottom: 4px;
  font-weight: 500;
}

/* Markdown 样式 */
.bot-md :deep(p) { margin: 0 0 0.8rem 0; }
.bot-md :deep(p):last-child { margin-bottom: 0; }
.bot-md :deep(h1), .bot-md :deep(h2), .bot-md :deep(h3), .bot-md :deep(h4) {
  margin: 1rem 0 0.5rem 0;
  font-weight: 600;
  color: #111827;
  line-height: 1.3;
}
.bot-md :deep(h1) { font-size: 1.3rem; }
.bot-md :deep(h2) { font-size: 1.15rem; }
.bot-md :deep(h3) { font-size: 1rem; }
.bot-md :deep(ul), .bot-md :deep(ol) { margin: 0.5rem 0 0.8rem 1.4rem; }
.bot-md :deep(li) { margin-bottom: 0.3rem; }
.bot-md :deep(strong) { color: #c2410c; font-weight: 600; }
.bot-md :deep(code) { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; }
.bot-md :deep(pre) { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; overflow-x: auto; margin: 0.8rem 0; }
.bot-md :deep(pre code) { background: transparent; padding: 0; }
.bot-md :deep(blockquote) { border-left: 3px solid #fb8600; padding: 4px 14px; margin: 0.8rem 0; color: #6b7280; background: #fff7ed; border-radius: 0 6px 6px 0; }

.message.user .msg-content :deep(code) {
  background: rgba(255,255,255,0.2);
  color: #fff;
}

/* 打字光标 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: #fb8600;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 状态条：流式时显示"后台正在干嘛" */
.status-line {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #fb8600;
  margin-bottom: 8px;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fb8600;
  animation: blink 1s infinite;
}

/* 图表卡片 + 邮件发送 */
.chart-card {
  width: 100%;
  max-width: 768px;
  margin: 0 auto 24px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
}
.chart-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}
.chart-box {
  width: 100%;
  height: 260px;
  margin-bottom: 8px;
}
.email-send {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}
.email-btn {
  background: #fb8600;
  border-color: #fb8600;
  color: #fff;
}
.email-btn:hover {
  background: #e67800;
  border-color: #e67800;
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-scroll {
    padding: 16px 12px 100px;
  }

  .msg-content {
    max-width: 100%;
    font-size: 0.9rem;
  }
}
</style>