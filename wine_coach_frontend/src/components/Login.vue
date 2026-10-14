<template>
  <div class="login-page">
    <div class="login-card">
      <div class="card-header">
        <span class="back-btn" @click="$router.push('/')">←</span>
        <h2>登录</h2>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" class="login-form">
        <el-form-item prop="user_name">
          <el-input
            v-model="form.user_name"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>

      <div class="card-footer">
        <span>还没有账号？</span>
        <span class="link" @click="$router.push('/register')">立即注册</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { storeAuth } from '../utils/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  user_name: '',
  password: ''
})

const rules = {
  user_name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const res = await axios.post('/users/login', {
        user_name: form.user_name,
        password: form.password
      })

      if (res.data.code === 200) {
        const token = res.data.data  // 后端返回 JWT 字符串
        storeAuth(token, form.user_name)
        ElMessage.success('登录成功')
        router.push('/chat')
      }
    } catch (err) {
      const msg = err.response?.data?.detail || '登录失败'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: #ffffff;
  border-radius: 16px;
  padding: 40px 30px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  position: relative;
}

.back-btn {
  position: absolute;
  left: 0;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.back-btn:hover {
  color: #fb8600;
}

.card-header h2 {
  flex: 1;
  text-align: center;
  margin: 0;
  font-size: 24px;
  color: #333;
}

.login-form {
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  height: 48px;
  background: #fb8600;
  border: none;
  border-radius: 8px;
  font-size: 16px;
}

.submit-btn:hover {
  background: #e67800;
}

.card-footer {
  text-align: center;
  color: #666;
  font-size: 14px;
}

.link {
  color: #fb8600;
  cursor: pointer;
  margin-left: 5px;
}

.link:hover {
  text-decoration: underline;
}
</style>
