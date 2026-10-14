// 认证工具：token 解析与登录态管理

// 保存登录态：token + 用户名，并从 JWT payload 解码 role_name / email 存入 sessionStorage
export function storeAuth(token, userName) {
  sessionStorage.setItem('token', token)
  sessionStorage.setItem('user_name', userName)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    sessionStorage.setItem('role_name', payload.role_name || 'user')
    sessionStorage.setItem('email', payload.email || '')
  } catch (e) {
    sessionStorage.setItem('role_name', 'user')
    sessionStorage.setItem('email', '')
  }
}

// 清空登录态
export function clearAuth() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('user_name')
  sessionStorage.removeItem('role_name')
  sessionStorage.removeItem('email')
}
