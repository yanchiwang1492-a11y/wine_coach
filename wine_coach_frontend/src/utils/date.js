// 日期工具

// 把后端返回的时间戳（秒/毫秒）或 datetime 字符串格式化为中文日期
export function formatDate(dateStr) {
  if (!dateStr) return ''
  let date
  if (typeof dateStr === 'number' || /^\d+$/.test(String(dateStr))) {
    const n = Number(dateStr)
    date = new Date(n < 1e12 ? n * 1000 : n)
  } else {
    date = new Date(dateStr)
  }
  if (isNaN(date.getTime())) return ''
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
