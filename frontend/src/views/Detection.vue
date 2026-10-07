<template>
  <div class="page detection-page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">DETECTION WORKSPACE</span>
        <h1>检测工作台</h1>
        <p>{{ scene.label }} <span class="heading-separator">/</span> {{ sceneRole }}</p>
      </div>
      <div class="actions">
        <el-button @click="keyDialog = true"
          ><el-icon><Key /></el-icon><span>AI 配置</span></el-button
        ><el-button :disabled="!result" @click="exportResult"
          ><el-icon><Download /></el-icon><span>导出结果</span></el-button
        >
      </div>
    </div>
    <div class="scene-tabs" role="tablist" aria-label="检测场景">
      <button
        v-for="item in scenes"
        :key="item.value"
        role="tab"
        :aria-selected="scenario === item.value"
        :class="{ active: scenario === item.value }"
        :disabled="locked"
        @click="selectScene(item.value)"
      >
        <el-icon :style="{ color: item.color }"><component :is="item.icon" /></el-icon
        ><span>{{ item.label }}</span
        ><i v-if="scenario === item.value" class="tab-indicator"></i>
      </button>
    </div>
    <el-alert v-if="error" :title="error" type="error" show-icon @close="error = ''" />
    <div class="detection-layout">
      <aside class="control-panel">
        <div class="control-title">
          <h2>检测配置</h2>
          <span class="step-label">01</span>
        </div>
        <label class="field-label">输入来源</label>
        <div class="segment input-modes">
          <button
            v-for="item in modes"
            :key="item.value"
            :class="{ active: mode === item.value }"
            :disabled="locked"
            @click="setMode(item.value)"
          >
            <el-icon><component :is="item.icon" /></el-icon>{{ item.label }}
          </button>
        </div>
        <label class="field-label" for="model-picker"
          >场景模型 <span>{{ models.length }} 个可用</span></label
        >
        <el-select
          id="model-picker"
          v-model="selectedModel"
          aria-label="场景模型"
          placeholder="暂无匹配模型"
          :disabled="locked"
          :loading="modelBusy"
          @change="loadModel"
          ><el-option v-for="item in models" :key="item.path" :label="item.name" :value="item.path"
        /></el-select>
        <div class="model-state">
          <span class="status-label" :class="{ off: !ready }"
            ><i class="status-dot" :class="{ off: !ready }"></i
            >{{
              modelBusy ? '模型加载中' : ready ? `已就绪 · ${classes.length} 个类别` : '模型未就绪'
            }}</span
          ><button
            v-if="!ready && !modelBusy && selectedModel"
            class="retry-link"
            @click="loadModel"
          >
            重试
          </button>
        </div>
        <router-link
          v-if="!models.length && !modelBusy"
          class="resource-link"
          to="/dashboard/models"
          >前往模型资源 <el-icon><ArrowRight /></el-icon
        ></router-link>
        <div class="confidence-label">
          <label class="field-label" for="confidence">置信度阈值</label
          ><span class="mono">{{ confidence.toFixed(2) }}</span>
        </div>
        <el-slider
          id="confidence"
          v-model="confidence"
          aria-label="置信度阈值"
          :min="0.01"
          :max="0.95"
          :step="0.01"
          :disabled="locked"
          :format-tooltip="percent"
          @change="clearResult"
        />
        <div class="slider-labels">
          <span>0.01</span
          ><button
            :disabled="locked"
            @click="resetConfidence"
          >
            恢复默认</button
          ><span>0.95</span>
        </div>
        <p v-if="confidence < 0.15" class="threshold-note">
          <el-icon><Warning /></el-icon>低阈值结果可能包含较多误检
        </p>
        <div class="upload-divider"></div>
        <template v-if="mode !== 'camera'">
          <label class="field-label">待检测文件</label>
          <input
            ref="fileInput"
            class="hidden-file"
            type="file"
            :accept="mode === 'image' ? '.jpg,.jpeg,.png,.gif,.bmp' : '.mp4,.avi,.mov,.mkv'"
            :disabled="locked"
            @change="chooseFile($event.target.files[0])"
          />
          <button
            class="upload-drop"
            :class="{ 'is-dragging': dragging }"
            :disabled="locked"
            @click="fileInput.click()"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="dropFile"
          >
            <el-icon><UploadFilled /></el-icon
            ><strong>{{ file ? '更换文件' : '选择或拖入文件' }}</strong
            ><small>{{
              mode === 'image'
                ? 'JPG / PNG / GIF / BMP · ≤ 10 MB'
                : 'MP4 / AVI / MOV / MKV · ≤ 100 MB'
            }}</small>
          </button>
          <div v-if="file" class="selected-file">
            <el-icon><Document /></el-icon
            ><span :title="file.name"
              >{{ file.name }}<small>{{ (file.size / 1048576).toFixed(2) }} MB</small></span
            ><button
              class="icon-button"
              :disabled="locked"
              aria-label="移除文件"
              title="移除文件"
              @click="resetFile"
            >
              <el-icon><Close /></el-icon>
            </button>
          </div>
          <el-button
            class="run-button"
            type="primary"
            :disabled="!ready || !file || modelBusy"
            :loading="running"
            @click="detect"
            ><el-icon v-if="!running"><VideoPlay /></el-icon
            ><span>{{ running ? '正在检测' : result ? '重新检测' : '开始检测' }}</span></el-button
          >
        </template>
        <template v-else
          ><div class="camera-info">
            <el-icon><VideoCamera /></el-icon><span>本机摄像头</span>
          </div>
          <el-button
            class="run-button"
            :type="cameraActive ? 'danger' : 'primary'"
            :disabled="!ready || modelBusy || cameraStarting"
            :loading="cameraStarting"
            @click="cameraActive ? stopCamera() : startCamera()"
            ><el-icon><VideoCamera /></el-icon
            ><span>{{ cameraActive ? '停止检测' : '启动摄像头' }}</span></el-button
          ></template
        >
        <div class="config-foot">
          <el-icon><Lock /></el-icon
          ><span>{{
            mode === 'camera' ? '实时画面不保存到历史记录' : '检测结果保存到当前账号'
          }}</span>
        </div>
      </aside>
      <section class="output-panel">
        <div class="preview-toolbar">
          <div class="preview-title">
            <el-icon><View /></el-icon>
            <h2>视觉预览</h2>
            <el-tag v-if="result" size="small" type="success" effect="plain">{{
              mode === 'camera' ? '实时' : '已完成'
            }}</el-tag>
          </div>
          <div class="segment">
            <button
              :class="{ active: previewMode === 'original' }"
              :disabled="mode === 'camera'"
              @click="previewMode = 'original'"
            >
              原始文件</button
            ><button
              :class="{ active: previewMode === 'result' }"
              :disabled="!result || mode === 'camera'"
              @click="previewMode = 'result'"
            >
              检测结果
            </button>
          </div>
        </div>
        <div
          class="visual-stage"
          :class="{ 'has-media': !!mediaUrl || cameraActive }"
          v-loading="running"
          element-loading-text="正在进行目标检测…"
          element-loading-background="rgba(245,248,245,.9)"
        >
          <template v-if="mode === 'camera'"
            ><video
              ref="cameraVideo"
              autoplay
              muted
              playsinline
              :class="{ invisible: !cameraActive }"
            ></video
            ><canvas
              ref="cameraCanvas"
              class="camera-overlay"
              :class="{ invisible: !cameraActive }"
            ></canvas>
            <div v-if="!cameraActive" class="stage-empty">
              <el-icon><VideoCamera /></el-icon><strong>摄像头待启动</strong>
            </div></template
          >
          <template v-else-if="mediaUrl"
            ><el-image
              v-if="mode === 'image'"
              :src="mediaUrl"
              fit="contain"
              :preview-src-list="[mediaUrl]"
              preview-teleported
              ><template #error><div class="stage-empty">图片加载失败</div></template></el-image
            ><video
              v-else
              :key="mediaUrl"
              :src="mediaUrl"
              controls
              playsinline
              @error="error = '视频无法预览，请下载结果或更换视频编码'"
          /></template>
          <div v-else class="stage-empty">
            <span class="empty-crosshair"
              ><el-icon><Aim /></el-icon></span
            ><strong>等待检测素材</strong
            ><span>{{ mode === 'image' ? 'IMAGE' : 'VIDEO' }} / {{ scene.short }}</span>
          </div>
        </div>
        <div class="preview-footer">
          <span class="mono">{{
            file ? file.name : mode === 'camera' ? 'LIVE CAMERA' : 'NO SOURCE'
          }}</span
          ><span v-if="result"
            >{{ detections.length }} 个{{ mode === 'video' ? '采样目标' : '目标'
            }}<span v-if="elapsed"> · {{ elapsed }} s</span></span
          ><span v-else>等待检测</span>
        </div>
        <div class="result-metrics">
          <div>
            <span>目标{{ mode === 'video' ? '次数' : '数量' }}</span
            ><strong>{{ result ? detections.length : '--' }}</strong>
          </div>
          <div>
            <span>平均置信度</span><strong>{{ result ? percent(stats.avg) : '--' }}</strong>
          </div>
          <div>
            <span>最高置信度</span><strong>{{ result ? percent(stats.max) : '--' }}</strong>
          </div>
          <div>
            <span>低置信度目标</span
            ><strong :class="{ amber: stats.low }">{{ result ? stats.low : '--' }}</strong>
          </div>
        </div>
      </section>
    </div>
    <div class="result-bottom">
      <section class="targets-section">
        <div class="section-head">
          <h2>
            目标明细 <small v-if="result">{{ detections.length }}</small>
          </h2>
          <a
            v-if="resultUrl"
            :href="resultUrl"
            :download="fileName(resultUrl)"
            class="download-link"
            ><el-icon><Download /></el-icon> 下载结果文件</a
          >
        </div>
        <div class="table-shell">
          <el-table
            :data="detections.slice((targetPage - 1) * 8, targetPage * 8)"
            empty-text="暂无检测目标"
            ><el-table-column type="index" width="48" label="#" /><el-table-column
              prop="class"
              label="目标类别"
              min-width="130"
            /><el-table-column label="置信度" width="120"
              ><template #default="{ row }"
                ><span :class="{ amber: row.confidence < 0.6 }">{{
                  percent(row.confidence)
                }}</span></template
              ></el-table-column
            ><el-table-column label="位置 / XYXY" min-width="155"
              ><template #default="{ row }"
                ><span class="mono">{{
                  (row.bbox || []).map((n) => Math.round(n)).join(', ')
                }}</span></template
              ></el-table-column
            ></el-table
          >
        </div>
        <el-pagination
          v-if="detections.length > 8"
          v-model:current-page="targetPage"
          :page-size="8"
          :total="detections.length"
          layout="prev, pager, next"
          size="small"
          class="target-pagination"
        />
      </section>
      <section class="insights-section">
        <div class="section-head">
          <h2>
            <el-icon><ChatDotRound /></el-icon> AI 研判
          </h2>
          <el-tag size="small" effect="plain" type="info">{{ scene.short }}</el-tag>
        </div>
        <p v-if="!result" class="muted insight-empty">暂无检测上下文</p>
        <template v-else
          ><div class="tag-list">
            <el-tag
              v-for="(count, label) in stats.counts"
              :key="label"
              effect="plain"
              type="info"
              size="small"
              >{{ label }} × {{ count }}</el-tag
            >
          </div>
          <p class="analysis-summary">
            {{
              result.analysis?.conclusion ||
              (stats.low
                ? '存在低置信度目标，建议人工复核。'
                : detections.length
                ? '已完成当前画面检测。'
                : '当前阈值下未检测到目标。')
            }}
          </p>
          <div class="actions">
            <el-button
              type="primary"
              plain
              :loading="reportLoading"
              :disabled="locked"
              @click="generateReport"
              >生成报告</el-button
            ><el-button :disabled="locked" @click="chatOpen = true"
              >结果问答 <el-icon><ArrowRight /></el-icon
            ></el-button>
          </div>
          <div v-if="report" class="ai-report">
            <small>{{ reportAI ? 'DeepSeek 分析' : '本地基础报告' }}</small>
            <div class="text-block">{{ report }}</div>
          </div></template
        >
      </section>
    </div>
    <el-dialog v-model="keyDialog" title="AI 连接配置" width="460px"
      ><el-form label-position="top"
        ><el-form-item label="本次会话 API Key"
          ><el-input
            v-model="keyInput"
            type="password"
            show-password
            placeholder="留空使用服务端配置" /></el-form-item></el-form
      ><template #footer
        ><el-button @click="clearKey">清除会话 Key</el-button
        ><el-button type="primary" @click="saveKey">保存</el-button></template
      ></el-dialog
    >
    <el-dialog v-model="chatOpen" title="检测结果问答" width="640px"
      ><div class="chat-context">
        {{ snapshot?.scenarioLabel }} · {{ fileName(snapshot?.model) }} ·
        {{ detections.length }} 个目标
      </div>
      <div ref="chatBox" class="chat-log" aria-live="polite">
        <div v-if="!messages.length" class="empty-state">
          <el-icon><ChatDotRound /></el-icon><strong>这次检测结果可靠吗？</strong>
        </div>
        <div v-for="(message, i) in messages" :key="i" class="chat-row" :class="message.role">
          <small>{{
            message.role === 'user' ? '你' : message.local ? '本地回答' : '检测助手'
          }}</small>
          <p class="text-block">{{ message.content }}</p>
        </div>
        <div v-if="chatLoading" class="thinking">
          <el-icon class="spinner"><Loading /></el-icon>正在分析检测结果…
        </div>
      </div>
      <form class="chat-compose" @submit.prevent="sendChat">
        <el-input
          v-model="chatInput"
          aria-label="检测问题"
          placeholder="输入关于本次检测的问题"
          :disabled="chatLoading"
          maxlength="2000"
        /><el-button
          type="primary"
          :loading="chatLoading"
          :disabled="!chatInput.trim()"
          native-type="submit"
          >发送</el-button
        >
      </form></el-dialog
    >
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useStore } from 'vuex'
import { useRoute, onBeforeRouteLeave } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api, scenes, percent, fileName, saveFile } from '../lib/workspace'
const store = useStore(),
  route = useRoute()
const modes = [
  { value: 'image', label: '图片', icon: 'Picture' },
  { value: 'video', label: '视频', icon: 'VideoPlay' },
  { value: 'camera', label: '实时', icon: 'VideoCamera' },
]
const scenario = ref(
    scenes.some((s) => s.value === route.query.scene) ? route.query.scene : 'general'
  ),
  mode = ref('image')
const models = ref([]),
  selectedModel = ref(''),
  classes = ref([]),
  ready = ref(false),
  modelBusy = ref(false)
const file = ref(null),
  sourceUrl = ref(''),
  previewMode = ref('original'),
  result = ref(null),
  confidence = ref(scenario.value === 'pest' ? 0.05 : 0.25)
const error = ref(''),
  dragging = ref(false),
  running = ref(false),
  elapsed = ref(''),
  snapshot = ref(null),
  targetPage = ref(1)
const fileInput = ref(null),
  cameraVideo = ref(null),
  cameraCanvas = ref(null),
  cameraActive = ref(false),
  cameraStarting = ref(false)
const report = ref(''),
  reportLoading = ref(false),
  reportAI = ref(false),
  keyDialog = ref(false),
  keyInput = ref(sessionStorage.getItem('deepseek_api_key') || '')
const chatOpen = ref(false),
  chatInput = ref(''),
  messages = ref([]),
  chatLoading = ref(false),
  chatBox = ref(null)
let stream = null,
  cameraTimer = null,
  alive = true,
  cameraGeneration = 0
const scene = computed(() => scenes.find((s) => s.value === scenario.value))
const sceneRole = computed(
  () =>
    ({
      general: '通用目标检测助手',
      drone: '低空安全监测助手',
      fire: '安全预警助手',
      flower: '花卉识别助手',
      pest: '农业植保助手',
    }[scenario.value])
)
const locked = computed(
  () =>
    running.value ||
    modelBusy.value ||
    cameraActive.value ||
    cameraStarting.value ||
    reportLoading.value ||
    chatLoading.value
)
const detections = computed(() => result.value?.detections || [])
const resultUrl = computed(() => result.value?.result_image || result.value?.result_video || '')
const mediaUrl = computed(() =>
  previewMode.value === 'result' && resultUrl.value ? resultUrl.value : sourceUrl.value
)
const stats = computed(() => {
  const counts = Object.create(null)
  let total = 0,
    max = 0,
    low = 0
  for (const detection of detections.value) {
    const value = Number(detection.confidence || 0)
    total += value
    max = Math.max(max, value)
    low += value < 0.6 ? 1 : 0
    counts[detection.class] = (counts[detection.class] || 0) + 1
  }
  return { avg: detections.value.length ? total / detections.value.length : 0, max, low, counts }
})
function resetConfidence() {
  confidence.value = scenario.value === 'pest' ? 0.05 : 0.25
  clearResult()
}
function clearResult() {
  result.value = null
  snapshot.value = null
  report.value = ''
  messages.value = []
  previewMode.value = 'original'
  targetPage.value = 1
  elapsed.value = ''
}
function resetFile() {
  if (sourceUrl.value) URL.revokeObjectURL(sourceUrl.value)
  sourceUrl.value = ''
  file.value = null
  if (fileInput.value) fileInput.value.value = ''
  clearResult()
}
function setMode(value) {
  if (locked.value || mode.value === value) return
  stopCamera()
  resetFile()
  mode.value = value
}
async function selectScene(value) {
  if (locked.value || scenario.value === value) return
  scenario.value = value
  confidence.value = value === 'pest' ? 0.05 : 0.25
  clearResult()
  await loadScene()
}
async function loadScene() {
  modelBusy.value = true
  ready.value = false
  error.value = ''
  models.value = []
  selectedModel.value = ''
  try {
    const data = await api(`/models/scenario/${scenario.value}`)
    if (!alive) return
    models.value = data.models || []
    selectedModel.value =
      models.value.find((m) => m.path === route.query.model)?.path ||
      models.value.find((m) => m.path === data.current_model)?.path ||
      models.value[0]?.path ||
      ''
    if (selectedModel.value) await loadModel()
    else error.value = '该场景没有可用模型，请先在模型资源中上传。'
  } catch (e) {
    error.value = e.message
  } finally {
    modelBusy.value = false
  }
}
async function loadModel() {
  modelBusy.value = true
  ready.value = false
  clearResult()
  error.value = ''
  try {
    const data = await api('/models/load_by_scenario', {
      method: 'POST',
      data: { scenario: scenario.value, model_path: selectedModel.value },
    })
    if (!alive) return
    ready.value = data.current_model === selectedModel.value
    classes.value = data.model_info?.classes || []
    window.dispatchEvent(new Event('model-changed'))
  } catch (e) {
    error.value = e.message
    classes.value = []
  } finally {
    modelBusy.value = false
  }
}
function chooseFile(value) {
  dragging.value = false
  if (!value || locked.value) return
  const allowed = mode.value === 'image' ? /\.(jpe?g|png|gif|bmp)$/i : /\.(mp4|avi|mov|mkv)$/i
  if (!allowed.test(value.name)) {
    ElMessage.error('文件格式不支持当前检测方式')
    return
  }
  if (value.size > (mode.value === 'image' ? 10 : 100) * 1048576) {
    ElMessage.error('文件超过大小限制')
    return
  }
  resetFile()
  file.value = value
  sourceUrl.value = URL.createObjectURL(value)
  error.value = ''
}
function dropFile(event) {
  dragging.value = false
  chooseFile(event.dataTransfer.files[0])
}
function makeSnapshot() {
  return {
    scenario: scenario.value,
    scenarioLabel: scene.value.label,
    model: selectedModel.value,
    confidence: confidence.value,
    mode: mode.value,
    filename: file.value?.name || 'camera',
    time: new Date().toISOString(),
  }
}
async function detect() {
  if (!file.value || !ready.value || locked.value) return
  const context = makeSnapshot(),
    form = new FormData()
  form.append('file', file.value)
  form.append('user_id', store.state.user.id)
  form.append('confidence', context.confidence)
  form.append('model_path', context.model)
  clearResult()
  error.value = ''
  running.value = true
  const start = performance.now()
  try {
    const data = await api(`/detect_${mode.value}`, { method: 'POST', data: form, timeout: 0 })
    if (!alive) return
    result.value = data
    snapshot.value = context
    elapsed.value = ((performance.now() - start) / 1000).toFixed(1)
    previewMode.value = 'result'
  } catch (e) {
    error.value = e.message
  } finally {
    running.value = false
  }
}
async function startCamera() {
  if (!ready.value || locked.value) return
  cameraStarting.value = true
  error.value = ''
  clearResult()
  const generation = ++cameraGeneration
  try {
    const acquired = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    })
    if (!alive || generation !== cameraGeneration) {
      acquired.getTracks().forEach((t) => t.stop())
      return
    }
    stream = acquired
    cameraVideo.value.srcObject = stream
    await cameraVideo.value.play()
    if (!alive || generation !== cameraGeneration) {
      acquired.getTracks().forEach((t) => t.stop())
      return
    }
    cameraActive.value = true
    snapshot.value = makeSnapshot()
    processCamera(generation)
  } catch (e) {
    error.value = `摄像头启动失败：${e.message}`
    stopCamera()
  } finally {
    cameraStarting.value = false
  }
}
async function processCamera(generation) {
  if (!cameraActive.value || generation !== cameraGeneration) return
  const video = cameraVideo.value,
    canvas = cameraCanvas.value
  if (!video.videoWidth) {
    cameraTimer = setTimeout(() => processCamera(generation), 200)
    return
  }
  const source = document.createElement('canvas')
  source.width = video.videoWidth
  source.height = video.videoHeight
  source.getContext('2d').drawImage(video, 0, 0)
  try {
    const data = await api('/process_frame', {
      method: 'POST',
      data: {
        image: source.toDataURL('image/jpeg', 0.8),
        user_id: store.state.user.id,
        confidence: confidence.value,
        model_path: selectedModel.value,
      },
    })
    if (!alive || generation !== cameraGeneration) return
    result.value = data
    canvas.width = source.width
    canvas.height = source.height
    const ctx = canvas.getContext('2d')
    ctx.strokeStyle = '#69eea8'
    ctx.fillStyle = '#69eea8'
    ctx.lineWidth = 2
    ctx.font = '14px sans-serif'
    data.detections.forEach((d) => {
      const [x1, y1, x2, y2] = d.bbox
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
      ctx.fillText(`${d.class} ${percent(d.confidence)}`, Math.max(0, x1), Math.max(16, y1 - 5))
    })
    cameraTimer = setTimeout(() => processCamera(generation), 700)
  } catch (e) {
    if (generation === cameraGeneration) {
      error.value = e.message
      stopCamera()
    }
  }
}
function stopCamera() {
  ++cameraGeneration
  clearTimeout(cameraTimer)
  stream?.getTracks().forEach((t) => t.stop())
  stream = null
  cameraActive.value = false
}
function exportResult() {
  if (result.value)
    saveFile(
      JSON.stringify({ ...result.value, context: snapshot.value }, null, 2),
      `detection-${Date.now()}.json`
    )
}
function saveKey() {
  const key = keyInput.value.trim()
  if (key) sessionStorage.setItem('deepseek_api_key', key)
  else sessionStorage.removeItem('deepseek_api_key')
  keyDialog.value = false
  ElMessage.success('AI 配置已保存')
}
function clearKey() {
  sessionStorage.removeItem('deepseek_api_key')
  keyInput.value = ''
  keyDialog.value = false
}
function aiContext() {
  return {
    analysis: result.value?.analysis || {
      detection_type: mode.value,
      total_objects: detections.value.length,
      avg_confidence: stats.value.avg,
      max_confidence: stats.value.max,
      class_counts: stats.value.counts,
      review_required: !detections.value.length || stats.value.low > 0,
    },
    detections: detections.value,
    scenario: snapshot.value?.scenario,
    api_key: sessionStorage.getItem('deepseek_api_key') || '',
  }
}
async function generateReport() {
  if (!result.value || locked.value) return
  reportLoading.value = true
  try {
    const data = await api('/analysis/report', { method: 'POST', data: aiContext() })
    report.value = data.report
    reportAI.value = data.ai_enabled
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    reportLoading.value = false
  }
}
async function scrollChat() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}
async function sendChat() {
  const content = chatInput.value.trim()
  if (!content || chatLoading.value || !result.value) return
  const history = messages.value.map(({ role, content }) => ({ role, content }))
  messages.value.push({ role: 'user', content })
  chatInput.value = ''
  chatLoading.value = true
  scrollChat()
  try {
    const data = await api('/analysis/chat', {
      method: 'POST',
      data: { ...aiContext(), message: content, messages: history },
    })
    messages.value.push({ role: 'assistant', content: data.reply, local: !data.ai_enabled })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: e.message, local: true })
  } finally {
    chatLoading.value = false
    scrollChat()
  }
}
onMounted(loadScene)
onBeforeRouteLeave(() => {
  if (running.value || modelBusy.value) {
    ElMessage.info('当前任务完成后可切换页面')
    return false
  }
})
onBeforeUnmount(() => {
  alive = false
  stopCamera()
  if (sourceUrl.value) URL.revokeObjectURL(sourceUrl.value)
})
</script>
<style scoped>
.heading-separator {
  color: #b5bdb6;
  margin: 0 10px;
}
.scene-tabs {
  display: flex;
  gap: 22px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 24px;
  overflow-x: auto;
}
.scene-tabs button {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  padding: 0 5px 15px;
  border: 0;
  background: none;
  font-size: 13px;
  color: #7d8880;
}
.scene-tabs button.active {
  color: var(--ink);
  font-weight: 600;
}
.scene-tabs .el-icon {
  font-size: 17px;
}
.tab-indicator {
  position: absolute;
  bottom: 0;
  height: 2px;
  background: var(--accent);
  left: 0;
  right: 0;
}
.detection-layout {
  display: grid;
  grid-template-columns: 266px minmax(0, 1fr);
  border: 1px solid var(--line);
  border-radius: 7px;
  background: white;
  overflow: hidden;
}
.control-panel {
  padding: 22px;
  border-right: 1px solid var(--line);
}
.control-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
}
.control-title h2 {
  font-size: 14px;
}
.step-label {
  font: 12px monospace;
  color: #b2bbb4;
}
.field-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #5e6d62;
  margin: 19px 0 9px;
}
.field-label > span {
  font-size: 10px;
  color: #9fa8a1;
}
.input-modes {
  display: flex;
  width: 100%;
}
.input-modes button {
  flex: 1;
  padding: 5px 8px;
}
.control-panel .el-select {
  width: 100%;
}
.model-state {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}
.model-state .status-label {
  font-size: 10px;
}
.retry-link,
.slider-labels button {
  border: 0;
  padding: 0;
  background: none;
  color: var(--accent);
  font-size: 10px;
}
.resource-link {
  font-size: 11px;
  color: var(--accent);
}
.confidence-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 22px;
}
.confidence-label .field-label {
  margin: 0;
}
.confidence-label .mono {
  font-size: 13px;
}
.slider-labels {
  display: flex;
  justify-content: space-between;
  color: #a5ada6;
  font-size: 10px;
}
.threshold-note {
  display: flex;
  gap: 4px;
  align-items: center;
  font-size: 10px;
  color: #a47725;
  margin-top: 12px;
}
.upload-divider {
  border-top: 1px solid var(--line);
  margin-top: 24px;
}
.hidden-file {
  display: none;
}
.upload-drop {
  width: 100%;
  min-height: 119px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px dashed #cbd7cd;
  border-radius: 5px;
  background: #fbfdfb;
  color: #6b8072;
  padding: 13px 8px;
}
.upload-drop > .el-icon {
  font-size: 23px;
  color: #82998a;
}
.upload-drop strong {
  font-size: 12px;
  font-weight: 500;
}
.upload-drop small {
  font-size: 9px;
}
.upload-drop.is-dragging {
  background: #e4f1e7;
  border-color: var(--accent);
}
.selected-file {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 12px 0;
  font-size: 11px;
}
.selected-file > span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.selected-file small {
  display: block;
  font-size: 10px;
}
.selected-file .icon-button {
  width: 24px;
  height: 24px;
  border: 0;
  font-size: 13px;
}
.run-button {
  width: 100%;
  margin-top: 17px;
  height: 39px;
}
.config-foot {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  color: #9da69e;
  font-size: 10px;
  margin-top: 12px;
}
.camera-info {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 30px 0;
  color: var(--muted);
}
.output-panel {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.preview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  gap: 10px;
}
.preview-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.preview-title h2 {
  font-size: 13px;
}
.preview-title > .el-icon {
  color: #8d9b90;
}
.visual-stage {
  position: relative;
  min-height: 310px;
  flex: 1;
  background-color: #f7f9f7;
  background-image: repeating-linear-gradient(0deg, transparent, transparent 31px, #e9eee978 32px),
    repeating-linear-gradient(90deg, transparent, transparent 31px, #e9eee978 32px);
  display: flex;
  justify-content: center;
  align-items: center;
  height: 340px;
}
.visual-stage.has-media {
  background: #18231f;
}
.visual-stage > .el-image,
.visual-stage > video {
  width: 100%;
  height: 100%;
  position: absolute;
  inset: 0;
  object-fit: contain;
}
.visual-stage :deep(.el-image__inner) {
  object-fit: contain;
}
.camera-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: contain;
  inset: 0;
  pointer-events: none;
}
.invisible {
  visibility: hidden;
}
.stage-empty {
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 14px;
  color: #9aa99e;
}
.stage-empty strong {
  font-size: 14px;
  color: #83978a;
  font-weight: 400;
}
.stage-empty > span:last-child {
  font: 10px monospace;
  color: #a8b6ac;
}
.stage-empty > .el-icon {
  font-size: 35px;
}
.empty-crosshair {
  border: 1px solid #dae4dc;
  border-radius: 7px;
  width: 60px;
  height: 60px;
  display: grid;
  place-items: center;
  font-size: 30px;
  background: #fdfefd;
}
.preview-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 10px 20px;
  border-top: 1px solid var(--line);
  font-size: 10px;
  color: #8a978e;
}
.preview-footer .mono {
  font-size: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-footer > span:last-child {
  flex-shrink: 0;
}
.result-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  padding: 20px 0;
}
.result-metrics > div {
  padding: 0 20px;
  border-left: 1px solid var(--line);
}
.result-metrics > div:first-child {
  border: 0;
}
.result-metrics span {
  display: block;
  font-size: 10px;
  color: #939e96;
}
.result-metrics strong {
  font-size: 24px;
  font-weight: 500;
  color: #3d5145;
  font-variant-numeric: tabular-nums;
}
.amber {
  color: #af813b !important;
}
.result-bottom {
  margin-top: 28px;
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 30px;
}
.targets-section,
.insights-section {
  min-width: 0;
}
.result-bottom h2 {
  font-size: 14px;
}
.result-bottom h2 small {
  margin-left: 6px;
}
.download-link {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--accent);
}
.insights-section {
  padding-left: 25px;
  border-left: 1px solid var(--line);
}
.insights-section h2 {
  display: flex;
  align-items: center;
  gap: 7px;
}
.insight-empty {
  font-size: 12px;
  padding-top: 26px;
}
.analysis-summary {
  font-size: 12px;
  color: #809086;
  margin: 16px 0;
}
.ai-report {
  margin-top: 18px;
  border-top: 1px solid var(--line);
  padding-top: 14px;
}
.ai-report small {
  font-size: 10px;
  color: var(--accent);
}
.target-pagination {
  margin-top: 12px;
}
.chat-context {
  color: var(--muted);
  font-size: 11px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
  overflow-wrap: anywhere;
}
.chat-log {
  height: 340px;
  overflow-y: auto;
  padding: 12px 0;
}
.chat-row {
  padding: 12px 14px;
  margin: 10px 25px 10px 0;
  background: #f5f7f5;
  border-radius: 6px;
}
.chat-row.user {
  margin: 10px 0 10px 25px;
  background: #edf5ef;
}
.chat-row small {
  color: #8f9d93;
  font-size: 10px;
}
.chat-compose {
  display: flex;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}
.thinking {
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
}
@media (max-width: 1100px) {
  .detection-layout {
    grid-template-columns: 235px minmax(0, 1fr);
  }
  .control-panel {
    padding: 18px;
  }
  .preview-toolbar {
    padding: 14px;
  }
  .result-metrics > div {
    padding: 0 10px;
  }
  .result-metrics strong {
    font-size: 20px;
  }
  .scene-tabs {
    gap: 18px;
  }
}
@media (max-width: 760px) {
  .detection-layout {
    grid-template-columns: 1fr;
  }
  .control-panel {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .visual-stage {
    min-height: 250px;
    height: 300px;
  }
  .result-bottom {
    grid-template-columns: 1fr;
  }
  .insights-section {
    border: 0;
    border-top: 1px solid var(--line);
    padding: 20px 0 0;
  }
  .preview-title .el-tag {
    display: none;
  }
  .scene-tabs {
    gap: 14px;
  }
  .scene-tabs button {
    font-size: 12px;
  }
  .result-metrics {
    padding: 15px 0;
  }
  .result-metrics strong {
    font-size: 19px;
  }
}
</style>
