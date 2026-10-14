<template>
  <div class="input-area">
    <div class="input-wrapper">
      <el-input
        :model-value="inputText"
        @update:model-value="$emit('update:inputText', $event)"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :placeholder="isRecording ? '正在聆听…' : '输入消息，Enter 发送'"
        @keydown.enter="onEnterKey"
        ref="inputField"
        :disabled="isRecording && !inputText"
      />
      <div class="input-actions">
        <el-button
          class="icon-btn"
          :class="{ recording: isRecording }"
          @click="$emit('toggleVoice')"
          :disabled="!voskReady || isSending"
          :title="voskReady ? (isRecording ? '停止录音' : '语音输入') : '语音模型加载中'"
        >
          <template v-if="!isRecording">
            <el-icon><Microphone /></el-icon>
          </template>
          <template v-else>
            <el-icon><Close /></el-icon>
          </template>
        </el-button>
        <el-button
          class="send-btn"
          :class="{ loading: isSending }"
          @click="$emit('sendMessage')"
          :disabled="isSending || (!inputText.trim() && !isRecording)"
        >
          <el-icon v-if="isSending"><Loading /></el-icon>
          <el-icon v-else><Top /></el-icon>
        </el-button>
      </div>
    </div>
    <div class="input-hint">Enter 发送，Shift+Enter 换行</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Microphone, Close, Top, Loading } from '@element-plus/icons-vue'

defineProps({
  inputText: { type: String, default: '' },
  isSending: { type: Boolean, default: false },
  isRecording: { type: Boolean, default: false },
  voskReady: { type: Boolean, default: false },
})

const emit = defineEmits(['update:inputText', 'sendMessage', 'toggleVoice', 'enterKey'])

const inputField = ref(null)

// 回车发送（Shift+Enter 换行）——父组件通过 enterKey 事件真正发送
function onEnterKey(e) {
  if (e.shiftKey) return
  e.preventDefault()
  emit('enterKey')
}

function inputFocus() {
  if (inputField.value) inputField.value.focus()
}

defineExpose({ inputFocus })
</script>

<style scoped>
.input-area {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 20px 24px;
  background: linear-gradient(to bottom, rgba(255,255,255,0), #ffffff 30%);
  display: flex;
  justify-content: center;
  z-index: 10;
}

.input-wrapper {
  width: 100%;
  max-width: 768px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: border-color 0.2s, box-shadow 0.2s;
  overflow: hidden;
}

/* 左边橙色竖条 */
.input-wrapper::before {
  content: '';
  display: block;
  width: 4px;
  background: #fb8600;
  border-radius: 12px 0 0 12px;
  flex-shrink: 0;
}

.input-wrapper:focus-within {
  border-color: #fb8600;
  box-shadow: 0 0 0 3px rgba(230, 126, 34, 0.1);
}

.input-wrapper :deep(.el-textarea__inner) {
  background: transparent;
  color: #1f2937;
  border: none;
  box-shadow: none;
  resize: none;
  padding: 12px 8px 12px 12px;
}

.input-wrapper :deep(.el-textarea__inner::placeholder) {
  color: #9ca3af;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding-right: 8px;
}

.icon-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  color: #6b7280;
  flex-shrink: 0;
  font-size: 16px;
}

.icon-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #fb8600;
}

.icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.icon-btn.recording {
  background: #fef2f2;
  color: #ef4444;
}

.send-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: #fb8600;
  color: #ffffff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  font-size: 14px;
}

.send-btn:hover:not(:disabled) {
  background: #e67800;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: #fed7aa;
  cursor: not-allowed;
}

.send-btn.loading {
  background: #fbbf24;
}

.input-hint {
  position: absolute;
  bottom: 4px;
  font-size: 0.72rem;
  color: #d1d5db;
  text-align: center;
  width: 100%;
  pointer-events: none;
}

/* 响应式 */
@media (max-width: 768px) {
  .input-area {
    padding: 12px 12px 18px;
  }
}
</style>