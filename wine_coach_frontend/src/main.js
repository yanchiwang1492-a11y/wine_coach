import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from 'axios'
import App from './App.vue'
import router from './router'

// ========== axios 全局配置 ==========
// 使用相对路径，通过 Vite 代理访问后端
axios.defaults.baseURL = ''
axios.defaults.headers.post['Content-Type'] = 'application/json'

// 请求拦截器：自动附加 JWT token（对齐 wine_max：sessionStorage + Authorization Bearer）
axios.interceptors.request.use(config => {
  const token = sessionStorage.getItem('token')
  if (token) {
    config.headers['Authorization'] = 'Bearer ' + token
  }
  return config
}, error => Promise.reject(error))

// 响应拦截器：任何接口返回 401（token失效/已退出），清登录态跳回登录页
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user_name')
      sessionStorage.removeItem('role_name')
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
