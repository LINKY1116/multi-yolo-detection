<template>
  <div class="assistant-widget" :class="{ open: panelOpen, minimized: !panelOpen }">
    <button class="assistant-avatar" @click="panelOpen = !panelOpen" title="检测助手">
      <span class="face">
        <i></i>
        <i></i>
      </span>
      <span class="pulse"></span>
    </button>

    <transition name="assistant-panel">
      <div v-if="panelOpen" class="assistant-panel">
        <div class="assistant-head">
          <div>
            <strong>小 Y 检测助手</strong>
            <p>我可以解释项目功能和页面分布</p>
          </div>
          <button class="close-btn" @click="panelOpen = false">×</button>
        </div>

        <div class="assistant-tip">
          <span>{{ currentTip }}</span>
        </div>

        <div class="quick-actions">
          <button v-for="action in actions" :key="action.text" @click="go(action.path)">
            <el-icon><component :is="action.icon" /></el-icon>
            {{ action.text }}
          </button>
        </div>

        <div class="assistant-qa">
          <div class="qa-title">项目问答</div>
          <div class="qa-suggestions">
            <button v-for="question in suggestedQuestions" :key="question" @click="ask(question)">
              {{ question }}
            </button>
          </div>
          <div class="qa-answer">
            <span v-if="qaLoading">小 Y 正在思考...</span>
            <span v-else>{{ answer }}</span>
          </div>
          <div class="qa-input">
            <input
              v-model="questionInput"
              placeholder="问我：模型怎么命名？AI角色怎么切换？"
              @keyup.enter="ask(questionInput)"
            >
            <button @click="ask(questionInput)" :disabled="qaLoading">
              {{ qaLoading ? '思考中' : '问' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { Camera, Clock, Setting, House } from '@element-plus/icons-vue'

export default {
  name: 'FloatingAssistant',
  components: { Camera, Clock, Setting, House },
  data() {
    return {
      panelOpen: true,
      tipIndex: 0,
      timer: null,
      tips: [
        '上传图片前可以先确认当前模型是否适合检测场景。',
        '视频检测耗时更长，检测时可以留意页面的加载提示。',
        '历史记录里可以复查每次检测的置信度与结果文件。',
        'AI 分析适合用来写答辩说明和解释检测结果。'
      ],
      actions: [
        { text: '回首页', path: '/dashboard/home', icon: 'House' },
        { text: '去检测', path: '/dashboard/detection', icon: 'Camera' },
        { text: '看历史', path: '/dashboard/history', icon: 'Clock' },
        { text: '换模型', path: '/dashboard/models', icon: 'Setting' }
      ],
      questionInput: '',
      answer: '你可以问我系统有哪些功能、每个页面做什么、模型怎么命名、检测流程怎么走。',
      suggestedQuestions: ['功能分布', '怎么检测', '模型命名', 'AI角色'],
      qaLoading: false
    }
  },
  computed: {
    currentTip() {
      return this.tips[this.tipIndex]
    }
  },
  mounted() {
    this.timer = setInterval(() => {
      this.tipIndex = (this.tipIndex + 1) % this.tips.length
    }, 4500)
  },
  beforeUnmount() {
    clearInterval(this.timer)
  },
  methods: {
    go(path) {
      this.$router.push(path)
      this.panelOpen = false
    },
    async ask(question) {
      const text = String(question || '').trim()
      if (!text) return
      this.questionInput = ''
      this.qaLoading = true
      this.answer = '小 Y 正在思考，我会先整理项目功能和模块信息...'
      try {
        const response = await fetch('/api/project_assistant/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: text
          })
        })
        const data = await response.json()
        if (data.success && data.reply) {
          this.answer = data.reply
        } else {
          this.answer = this.getAnswer(text)
        }
      } catch {
        this.answer = this.getAnswer(text)
      } finally {
        this.qaLoading = false
      }
    },
    getAnswer(question) {
      const q = question.toLowerCase()
      if (q.includes('模型') || q.includes('命名') || q.includes('名字')) {
        return '模型命名用于自动切换：drone_yolov8.pt 对应无人机，fire_yolov8.pt 对应火灾，flower_yolov8.pt 对应花卉，pest_yolov8.pt 对应病虫害。通用检测使用默认 models/yolov8n.pt。'
      }
      if (q.includes('ai') || q.includes('角色') || q.includes('问答')) {
        return 'AI 会根据检测页选择的场景切换角色：无人机是低空安全监测助手，火灾是安全预警助手，花卉是花卉识别助手，病虫害是农业植保助手，通用检测是通用目标检测助手。'
      }
      if (q.includes('检测') || q.includes('流程') || q.includes('怎么用')) {
        return '使用流程是：先在模型管理上传模型，再到检测页选择场景，系统自动加载对应模型，然后上传图片/视频或打开摄像头，检测完成后查看结果并生成 AI 报告或继续问答。'
      }
      if (q.includes('历史') || q.includes('记录')) {
        return '检测历史页面保存图片和视频检测记录，可以查看检测时间、文件、目标数量、置信度、结果预览，也支持下载和删除记录。'
      }
      if (q.includes('功能') || q.includes('页面') || q.includes('分布') || q.includes('模块')) {
        return '系统主要分为：首页展示项目入口，目标检测页负责图片/视频/摄像头检测和 AI 分析，模型管理页负责上传、加载和删除模型，检测历史页负责记录查看、下载和清理。后端负责模型推理、文件处理、MySQL 存储和 DeepSeek 调用。'
      }
      return '这个项目是多场景 YOLO 目标检测平台，核心功能包括模型管理、图片检测、视频检测、摄像头实时检测、历史记录、AI 报告和智能问答。你可以问我“功能分布”“模型命名”“AI角色”“怎么检测”。'
    }
  }
}
</script>

<style scoped>
.assistant-widget {
  position: fixed;
  right: 26px;
  bottom: 26px;
  z-index: 30;
  display: flex;
  align-items: flex-end;
  gap: 14px;
}

.assistant-avatar {
  position: relative;
  width: 68px;
  height: 68px;
  border: 0;
  border-radius: 24px;
  cursor: pointer;
  background:
    radial-gradient(circle at 35% 20%, rgba(255,255,255,.95), rgba(255,255,255,.42) 28%, transparent 29%),
    linear-gradient(135deg, #b8d7ff, #d7c7ff 55%, #ffd9c5);
  box-shadow: 0 18px 36px rgba(129, 140, 248, .28);
  transition: transform .22s ease, box-shadow .22s ease;
  animation: mascotFloat 3.4s ease-in-out infinite;
}

.assistant-avatar:hover {
  transform: translateY(-4px) rotate(-2deg);
  box-shadow: 0 24px 44px rgba(129, 140, 248, .36);
}

.assistant-widget.open .assistant-avatar {
  display: none;
}

.face {
  position: absolute;
  left: 14px;
  right: 14px;
  top: 22px;
  display: flex;
  justify-content: space-between;
}

.face i {
  width: 12px;
  height: 14px;
  display: block;
  border-radius: 999px;
  background: #5267d8;
  box-shadow: inset 0 -4px 0 rgba(255, 255, 255, .35);
  animation: blink 4.2s infinite;
}

.pulse {
  position: absolute;
  inset: -8px;
  border-radius: 30px;
  border: 1px solid rgba(129, 140, 248, .22);
  animation: pulse 2.6s ease-out infinite;
}

.assistant-panel {
  width: 300px;
  padding: 16px;
  border: 1px solid rgba(226, 232, 240, .88);
  border-radius: 26px;
  background: rgba(255, 255, 255, .86);
  box-shadow: 0 26px 60px rgba(71, 85, 105, .16);
  backdrop-filter: blur(20px);
}

.assistant-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.assistant-head strong {
  color: #27304f;
  font-size: 16px;
  font-weight: 950;
}

.assistant-head p {
  margin: 6px 0 0;
  color: #7d89a5;
  font-size: 12px;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 999px;
  background: rgba(241, 245, 249, .85);
  color: #8190ad;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.assistant-tip {
  margin: 14px 0;
  padding: 12px 13px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(239, 246, 255, .92), rgba(245, 243, 255, .92));
  color: #52607d;
  font-size: 13px;
  line-height: 1.65;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.quick-actions button {
  height: 42px;
  border: 1px solid rgba(214, 226, 242, .92);
  border-radius: 15px;
  color: #52607d;
  background: rgba(255, 255, 255, .86);
  cursor: pointer;
  font-weight: 850;
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease, background .2s ease;
}

.quick-actions button:hover {
  transform: translateY(-2px);
  border-color: rgba(165, 180, 252, .76);
  background: #ffffff;
  box-shadow: 0 12px 22px rgba(129, 140, 248, .13);
}

.assistant-qa {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(226, 232, 240, .9);
}

.qa-title {
  color: #27304f;
  font-size: 13px;
  font-weight: 950;
  margin-bottom: 10px;
}

.qa-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.qa-suggestions button {
  height: 30px;
  padding: 0 10px;
  border: 1px solid rgba(196,181,253,.68);
  border-radius: 999px;
  color: #5b63d8;
  background: rgba(245,243,255,.82);
  cursor: pointer;
  font-size: 12px;
  font-weight: 850;
}

.qa-answer {
  min-height: 54px;
  max-height: 130px;
  overflow-y: auto;
  padding: 10px 11px;
  border-radius: 15px;
  background: rgba(248,250,252,.92);
  color: #52607d;
  font-size: 12px;
  line-height: 1.65;
}

.qa-input {
  display: grid;
  grid-template-columns: 1fr 42px;
  gap: 8px;
  margin-top: 10px;
}

.qa-input input {
  min-width: 0;
  height: 36px;
  padding: 0 10px;
  border: 1px solid rgba(214,226,242,.92);
  border-radius: 13px;
  outline: none;
  color: #42506f;
  background: rgba(255,255,255,.92);
}

.qa-input input:focus {
  border-color: rgba(129,140,248,.75);
}

.qa-input button {
  height: 36px;
  border: 0;
  border-radius: 13px;
  color: #fff;
  background: linear-gradient(135deg, #8b5cf6, #60a5fa);
  cursor: pointer;
  font-weight: 900;
}

.assistant-panel-enter-active,
.assistant-panel-leave-active {
  transition: opacity .22s ease, transform .22s ease;
}

.assistant-panel-enter-from,
.assistant-panel-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(.96);
}

@keyframes mascotFloat {
  0%, 100% { translate: 0 0; }
  50% { translate: 0 -8px; }
}

@keyframes blink {
  0%, 92%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(.12); }
}

@keyframes pulse {
  0% { opacity: .75; transform: scale(.88); }
  100% { opacity: 0; transform: scale(1.25); }
}

@media (max-width: 768px) {
  .assistant-widget {
    right: 16px;
    bottom: 16px;
    align-items: flex-end;
  }

  .assistant-panel {
    position: fixed;
    right: 16px;
    bottom: 94px;
    width: calc(100vw - 32px);
    max-width: 340px;
  }
}
</style>
