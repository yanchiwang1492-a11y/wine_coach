<template>
  <div class="home">
    <div class="home-bg">
      <img src="@/assets/wine_coach_homepage.png" alt="WineCoach" class="bg-image" />
    </div>
    <div class="home-overlay"></div>

    <div class="home-content">
      <div class="logo-area">
        <div class="logo-icon">🍷</div>
        <h1 class="logo-title">WineCoach</h1>
        <p class="logo-subtitle">葡萄酒销售实战模拟平台</p>
      </div>

      <!-- 已登录：进入聊天 / 退出登录 -->
      <div class="action-area" v-if="isLoggedIn">
        <p class="welcome-text">欢迎，{{ userName }}</p>
        <el-button type="primary" class="action-btn login-btn" @click="$router.push('/chat')">
          进入聊天
        </el-button>
        <el-button class="action-btn register-btn" @click="logout">
          退出登录
        </el-button>
      </div>

      <!-- 未登录：登录/注册 -->
      <div class="action-area" v-else>
        <el-button type="primary" class="action-btn login-btn" @click="$router.push('/login')">
          登录
        </el-button>
        <el-button class="action-btn register-btn" @click="$router.push('/register')">
          注册
        </el-button>
      </div>

      <div class="features">
        <div class="feature-item">
          <span class="feature-icon">🎯</span>
          <div class="feature-info">
            <span class="feature-text">个性化出题</span>
            <span class="feature-sub">根据你的销售场景智能选题</span>
          </div>
        </div>
        <div class="feature-item">
          <span class="feature-icon">📚</span>
          <div class="feature-info">
            <span class="feature-text">四维实战训练</span>
            <span class="feature-sub">知识 · 话术 · 情景应对 · 产品推荐</span>
          </div>
        </div>
        <div class="feature-item">
          <span class="feature-icon">📊</span>
          <div class="feature-info">
            <span class="feature-text">智能评价</span>
            <span class="feature-sub">雷达图 + 柱状图可视化得分</span>
          </div>
        </div>
        <div class="feature-item">
          <span class="feature-icon">🎙️</span>
          <div class="feature-info">
            <span class="feature-text">语音输入</span>
            <span class="feature-sub">支持语音实时转文字答题</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { clearAuth } from '../utils/auth'

const isLoggedIn = ref(!!sessionStorage.getItem('token'))
const userName = ref(sessionStorage.getItem('user_name') || '')

function logout() {
  axios.post('/users/logout').finally(() => {
    clearAuth()
    isLoggedIn.value = false
    userName.value = ''
  })
}
</script>

<style scoped>
.home {
  width: 100%;
  height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a2e;
}

.home-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.bg-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.6;
}

.home-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(26, 26, 46, 0.85) 0%, rgba(251, 134, 0, 0.3) 100%);
}

.home-content {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 40px;
}

.logo-area {
  margin-bottom: 50px;
}

.logo-icon {
  font-size: 80px;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.logo-title {
  font-size: 48px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 10px 0;
  letter-spacing: -1px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.logo-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
}

.action-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 60px;
}

.welcome-text {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  margin: 0;
}

.action-btn {
  width: 180px;
  height: 48px;
  font-size: 16px;
  border-radius: 24px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-btn {
  background: #fb8600;
  color: #ffffff;
}

.login-btn:hover {
  background: #e67800;
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(251, 134, 0, 0.4);
}

.register-btn {
  background: transparent;
  color: #ffffff;
  border: 2px solid #ffffff;
}

.register-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.features {
  display: flex;
  gap: 40px;
  justify-content: center;
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.9);
  text-align: left;
}

.feature-icon {
  font-size: 28px;
}

.feature-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-text {
  font-weight: 600;
  font-size: 15px;
}

.feature-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
}
</style>
