<template>
  <div class="chat-header">
    <div class="header-left">
      <el-button class="mobile-menu-btn" text @click="$emit('toggleSidebar')">
        <el-icon><Menu /></el-icon>
      </el-button>
      <div class="nav-group">
        <el-button text class="home-btn" @click="$emit('goHome')" title="返回主页">
          <el-icon><HomeFilled /></el-icon>
        </el-button>
        <el-button text class="back-btn" @click="$emit('backToSelect')" title="返回选择">
          <el-icon><Grid /></el-icon>
        </el-button>
      </div>
      <span class="chat-title">{{ chatTitle }}</span>
    </div>
    <div class="header-right">
      <span class="user-name">{{ userName }}</span>
      <el-button text class="logout-btn" @click="$emit('logout')" title="退出登录">
        <el-icon><SwitchButton /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { Menu, HomeFilled, SwitchButton, Grid } from '@element-plus/icons-vue'

defineProps({
  userName: { type: String, default: '' },
  chatTitle: { type: String, default: '' },
})

defineEmits(['logout', 'goHome', 'backToSelect', 'toggleSidebar'])
</script>

<style scoped>
.chat-header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.nav-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* 去掉 el-button 默认的相邻间距 */
.nav-group :deep(.el-button) {
  margin-left: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.chat-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-name {
  font-size: 0.85rem;
  color: #374151;
  font-weight: 500;
}

.logout-btn {
  color: #6b7280;
}

.logout-btn:hover {
  color: #fb8600;
}

.home-btn {
  color: #6b7280;
}

.home-btn:hover {
  color: #fb8600;
}

.back-btn {
  color: #6b7280;
}

.back-btn:hover {
  color: #fb8600;
}

.mobile-menu-btn {
  display: none;
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: block;
  }
}
</style>