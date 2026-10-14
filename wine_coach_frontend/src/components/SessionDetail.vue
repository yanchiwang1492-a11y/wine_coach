<template>
  <div class="session-detail-page">
    <div class="detail-header">
      <el-button text @click="$router.push('/history')" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回历史
      </el-button>
      <div class="header-info">
        <h2 class="detail-title">{{ sessionTitle }}</h2>
        <span class="detail-date">{{ formatDate(updatedAt) }}</span>
      </div>
    </div>

    <div class="detail-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else class="message-list">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message"
          :class="msg.role"
        >
          <div class="msg-avatar">
            {{ msg.role === 'user' ? '我' : 'W' }}
          </div>
          <div class="msg-content">
            <div class="msg-role-label" v-if="msg.role === 'assistant'">WineCoach</div>
            <div v-if="msg.role === 'assistant'" class="bot-md" v-html="formatMessage(msg.content)"></div>
            <template v-else>{{ msg.content }}</template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import { formatDate } from '../utils/date'
import { formatMessage } from '../utils/markdown'

const route = useRoute()
const router = useRouter()

const sessionTitle = ref('会话详情')
const updatedAt = ref('')
const messages = ref([])
const loading = ref(true)

function loadSession() {
  const sessionId = route.params.id
  if (!sessionId) {
    router.push('/history')
    return
  }

  axios.get(`/history/${sessionId}`)
    .then(res => {
      const data = res.data.data || {}
      sessionTitle.value = data.title || '会话详情'
      updatedAt.value = data.updated_at || ''
      messages.value = (data.messages || []).map(m => ({
        role: m.role,
        content: m.content
      }))
      loading.value = false
    })
    .catch(err => {
      console.error('加载会话失败:', err)
      loading.value = false
    })
}

onMounted(() => {
  loadSession()
})
</script>

<style scoped>
.session-detail-page {
  min-height: 100vh;
  background: #f9fafb;
}

.detail-header {
  background: #fff;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-info {
  flex: 1;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.detail-date {
  font-size: 13px;
  color: #9ca3af;
}

.detail-content {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message {
  display: flex;
  gap: 16px;
  max-width: 768px;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.message.user .msg-avatar {
  background: #fb8600;
  color: #ffffff;
}

.message.assistant .msg-avatar {
  background: #fff7ed;
  color: #fb8600;
  border: 1px solid #fed7aa;
}

.msg-content {
  flex: 1;
  line-height: 1.7;
  font-size: 15px;
}

.message.user .msg-content {
  background: #fb8600;
  color: #ffffff;
  padding: 12px 18px;
  border-radius: 18px;
  border-top-right-radius: 4px;
  word-break: break-word;
}

.message.assistant .msg-content {
  background: #ffffff;
  color: #1f2937;
  padding: 16px 20px;
  border-radius: 18px;
  border-top-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.msg-role-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
  font-weight: 500;
}

/* Markdown 样式 */
.bot-md :deep(p) { margin: 0 0 0.8rem 0; }
.bot-md :deep(p):last-child { margin-bottom: 0; }
.bot-md :deep(ul), .bot-md :deep(ol) { margin: 0.5rem 0 0.8rem 1.4rem; }
.bot-md :deep(li) { margin-bottom: 0.3rem; }
.bot-md :deep(strong) { color: #c2410c; font-weight: 600; }
.bot-md :deep(code) { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }
</style>
