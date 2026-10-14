<template>
  <div class="sidebar" :class="{ open: sidebarOpen }">
    <div class="sidebar-header">
      <div class="sidebar-brand">
        <span class="sidebar-brand-icon">🍷</span>
        WineCoach
      </div>
      <el-button class="new-chat-btn" @click="$emit('createSession')">
        <el-icon><Plus /></el-icon>
        新建对话
      </el-button>
    </div>

    <div class="sidebar-search">
      <el-input
        :model-value="searchKeyword"
        @update:model-value="$emit('update:searchKeyword', $event)"
        placeholder="搜索历史对话"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <div class="sidebar-list">
      <div
        v-for="session in filteredSessions"
        :key="session.session_id"
        class="session-item"
        :class="{ active: currentSessionId === session.session_id }"
        @click="$emit('switchSession', session.session_id)"
      >
        <span class="session-item-icon">💬</span>
        <span class="session-item-title">{{ session.title }}</span>
        <el-button class="session-delete-btn" text @click.stop="$emit('deleteSession', session.session_id)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
      <div v-if="filteredSessions.length === 0" class="no-sessions">
        暂无匹配的对话
      </div>
    </div>
  </div>

  <!-- 移动端遮罩 -->
  <div class="sidebar-overlay" :class="{ show: sidebarOpen }" @click="$emit('closeSidebar')"></div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, Delete, Search } from '@element-plus/icons-vue'

const props = defineProps({
  sessions: { type: Array, default: () => [] },
  currentSessionId: { type: String, default: null },
  searchKeyword: { type: String, default: '' },
  sidebarOpen: { type: Boolean, default: false },
})

defineEmits(['update:searchKeyword', 'createSession', 'switchSession', 'deleteSession', 'closeSidebar'])

// 会话搜索过滤（按标题模糊匹配）
const filteredSessions = computed(() => {
  const kw = props.searchKeyword.trim().toLowerCase()
  if (!kw) return props.sessions
  return props.sessions.filter(s => s.title.toLowerCase().indexOf(kw) > -1)
})
</script>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px 14px 12px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.sidebar-brand {
  font-size: 1.05rem;
  font-weight: 700;
  color: #fb8600;
  letter-spacing: -0.01em;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-brand-icon {
  width: 28px;
  height: 28px;
  background: #fff7ed;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-search {
  padding: 10px 14px;
  flex-shrink: 0;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 8px;
}

.session-item {
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.12s;
  margin-bottom: 2px;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-item:hover {
  background: #f3f4f6;
}

.session-item.active {
  background: #fff7ed;
  color: #c2410c;
  font-weight: 500;
}

.session-item-icon {
  font-size: 0.8rem;
  opacity: 0.7;
  flex-shrink: 0;
}

.session-item-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-delete-btn {
  opacity: 0;
  flex-shrink: 0;
}

.session-item:hover .session-delete-btn {
  opacity: 1;
}

.no-sessions {
  padding: 20px 12px;
  text-align: center;
  color: #9ca3af;
  font-size: 0.82rem;
}

/* 遮罩层 */
.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.3);
  z-index: 99;
}

.sidebar-overlay.show {
  display: block;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -260px;
    top: 0;
    bottom: 0;
    z-index: 100;
    transition: left 0.3s;
  }

  .sidebar.open {
    left: 0;
  }
}
</style>