<template>
  <div class="history-page">
    <div class="history-header">
      <el-button text @click="$router.push('/chat')" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回聊天
      </el-button>
      <h2 class="history-title">历史记录</h2>
    </div>

    <div class="history-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="sessions.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <div class="empty-text">暂无历史记录</div>
        <el-button type="primary" @click="$router.push('/chat')">开始新对话</el-button>
      </div>

      <div v-else class="session-list">
        <div
          v-for="session in sessions"
          :key="session.session_id"
          class="session-card"
          @click="viewSession(session.session_id)"
        >
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-date">{{ formatDate(session.updated_at) }}</div>
          </div>
          <div class="session-actions">
            <el-button text size="small" @click.stop="renameSession(session.session_id)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text size="small" type="danger" @click.stop="deleteSession(session.session_id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Edit, Delete, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import { formatDate } from '../utils/date'

const router = useRouter()
const sessions = ref([])
const loading = ref(true)

function loadSessions() {
  axios.get('/history/')
    .then(res => {
      sessions.value = res.data.data || []
      loading.value = false
    })
    .catch(err => {
      console.error('加载会话失败:', err)
      loading.value = false
    })
}

function viewSession(sessionId) {
  router.push(`/history/${sessionId}`)
}

function renameSession(sessionId) {
  const session = sessions.value.find(s => s.session_id === sessionId)
  if (!session) return

  const newTitle = prompt('请输入新的会话标题:', session.title)
  if (!newTitle || newTitle.trim() === session.title) return

  axios.patch(`/history/${sessionId}`, null, { params: { title: newTitle.trim() } })
    .then(() => {
      session.title = newTitle.trim()
    })
    .catch(err => {
      console.error('重命名失败:', err)
    })
}

function deleteSession(sessionId) {
  if (!confirm('确定删除这个会话吗？')) return

  axios.delete(`/history/${sessionId}`)
    .then(() => {
      sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    })
    .catch(err => {
      console.error('删除失败:', err)
    })
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.history-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.history-header {
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

.history-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.history-content {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  margin-bottom: 20px;
  font-size: 16px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.session-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.session-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.session-info {
  flex: 1;
}

.session-title {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.session-date {
  font-size: 13px;
  color: #9ca3af;
}

.session-actions {
  display: flex;
  gap: 8px;
}
</style>
