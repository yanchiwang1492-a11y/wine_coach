import axios from 'axios'

// 聊天接口：SSE 流式对话封装
// 用原生 fetch 逐块读取 body（axios 不支持流式），把后端事件流转成回调

// data: {"kind":"status","text":"正在分析..."}\n\n
// data: {"kind":"token","text":"处理"}\n\n
// data: {"kind":"token","text":"异议"}\n\n
// data: {"kind":"chart","data":[1,2,3]}\n\n

export async function streamChat({ question, sessionId, signal, onStatus, onToken, onChart, onError }) {
  const token = sessionStorage.getItem('token') || ''
  const params = new URLSearchParams({ question, session_id: sessionId })
  const resp = await fetch(`/chat/stream?${params}`, {
    headers: { Authorization: 'Bearer ' + token },
    signal
  })
  if (!resp.ok || !resp.body) throw new Error('HTTP ' + resp.status)

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const events = buffer.split('\n\n')
    buffer = events.pop() || ''
    for (const evt of events) {
      const line = evt.trim()
      if (!line.startsWith('data:')) continue
      const payload = line.slice(5).trim()
      if (!payload) continue

      let d
      try { d = JSON.parse(payload) } catch { continue }

      if (d.kind === 'status') onStatus?.(d.text)
      else if (d.kind === 'token') onToken?.(d.text)
      else if (d.kind === 'chart') onChart?.(d.data || [])
      else if (d.kind === 'error') onError?.(d.text)
    }
  }
}

// 查询会话练习进度（断点续传/进度展示用）
export async function getSessionProgress(sessionId) {
  const res = await axios.get('/chat/session_state', { params: { session_id: sessionId } })
  return res.data?.data || null
}
// “安全地层层取值，取不到就返回 null”，等价于：
// if (res.data && res.data.data) {
//     return res.data.data;
// } else {
//     return null;
// }