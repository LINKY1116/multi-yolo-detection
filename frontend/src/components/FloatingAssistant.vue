<template>
  <el-drawer
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="小 Y 助手"
    size="400px"
    class="project-assistant"
  >
    <div class="assistant-content">
      <div class="assistant-identity">
        <span
          ><el-icon><ChatDotRound /></el-icon
        ></span>
        <div>
          <strong>项目工作助手</strong><small>{{ busy ? '正在思考…' : 'Multi YOLO' }}</small>
        </div>
      </div>
      <div class="assistant-questions">
        <button
          v-for="question in questions"
          :key="question"
          :disabled="busy"
          @click="ask(question)"
        >
          {{ question }}<el-icon><ArrowRight /></el-icon>
        </button>
      </div>
      <div ref="log" class="assistant-log" aria-live="polite">
        <div
          v-for="(message, i) in messages"
          :key="i"
          class="assistant-message"
          :class="message.role"
        >
          <small>{{
            message.role === 'user' ? '你' : message.local ? '小 Y · 本地回答' : '小 Y · DeepSeek'
          }}</small>
          <p class="text-block">{{ message.content }}</p>
        </div>
        <div v-if="busy" class="assistant-thinking">
          <el-icon class="spinner"><Loading /></el-icon> 小 Y 正在思考…
        </div>
      </div>
      <form class="assistant-form" @submit.prevent="ask(input)">
        <el-input
          v-model="input"
          aria-label="向小Y提问"
          placeholder="输入项目相关问题"
          maxlength="2000"
          :disabled="busy"
        /><el-button
          type="primary"
          native-type="submit"
          :loading="busy"
          :disabled="!input.trim()"
          aria-label="发送问题"
          ><el-icon v-if="!busy"><Promotion /></el-icon
        ></el-button>
      </form>
    </div>
  </el-drawer>
</template>
<script setup>
import { ref, nextTick } from 'vue'
import { api } from '../lib/workspace'
defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])
const questions = ['怎么开始检测？', '模型如何命名？', '检测阈值是什么？', '如何导出检测结果？']
const input = ref(''),
  busy = ref(false),
  messages = ref([]),
  log = ref(null)
async function scroll() {
  await nextTick()
  if (log.value) log.value.scrollTop = log.value.scrollHeight
}
async function ask(question) {
  const text = question.trim()
  if (!text || busy.value) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  busy.value = true
  scroll()
  try {
    const data = await api('/project_assistant/chat', {
      method: 'POST',
      data: { message: text, api_key: sessionStorage.getItem('deepseek_api_key') || '' },
    })
    messages.value.push({ role: 'assistant', content: data.reply, local: !data.ai_enabled })
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: `暂时无法连接助手：${e.message}`,
      local: true,
    })
  } finally {
    busy.value = false
    scroll()
  }
}
</script>
<style>
.project-assistant.el-drawer {
  max-width: 100vw;
}
.project-assistant .el-drawer__header {
  border-bottom: 1px solid var(--line);
  margin-bottom: 0;
  padding: 22px;
  color: var(--ink);
  font-size: 16px;
}
.project-assistant .el-drawer__body {
  padding: 20px;
  min-height: 0;
}
</style>
<style scoped>
.assistant-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.assistant-identity {
  display: flex;
  gap: 11px;
  align-items: center;
  margin-bottom: 20px;
}
.assistant-identity > span {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border: 1px solid #d5e7d9;
  background: #edf5ef;
  border-radius: 8px;
  color: var(--accent);
  font-size: 23px;
}
.assistant-identity strong {
  font-size: 13px;
  font-weight: 500;
}
.assistant-identity small {
  display: block;
  font-size: 10px;
}
.assistant-questions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  margin-bottom: 16px;
}
.assistant-questions button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 0;
  border-bottom: 1px solid var(--line);
  padding: 9px 0;
  color: #78877c;
  background: none;
  font-size: 12px;
}
.assistant-log {
  flex: 1;
  overflow-y: auto;
  min-height: 80px;
}
.assistant-message {
  padding: 12px;
  background: #f6f8f6;
  margin: 8px 13px 8px 0;
  border-radius: 6px;
}
.assistant-message.user {
  background: #edf5ef;
  margin: 8px 0 8px 13px;
}
.assistant-message small {
  font-size: 10px;
  color: #92a097;
}
.assistant-form {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}
.assistant-form > .el-button {
  width: 38px;
  padding: 0;
}
.assistant-thinking {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 15px 0;
  color: var(--accent);
  font-size: 12px;
}
</style>
