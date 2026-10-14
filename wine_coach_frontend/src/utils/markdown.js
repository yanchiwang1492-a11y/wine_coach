// Markdown 渲染工具（marked 转 HTML + DOMPurify 防 XSS）
import { marked } from 'marked'
import DOMPurify from 'dompurify'

export function formatMessage(content) {
  if (!content) return ''
  try {
    return DOMPurify.sanitize(marked.parse(content))
  } catch (e) {
    return content.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}
