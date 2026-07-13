<template>
  <div class="detection-container">
    <!-- 检测方式选择 -->
    <el-card class="mode-selector" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>检测方式选择</span>
        </div>
      </template>

      <el-radio-group v-model="detectionMode" size="large" @change="handleModeChange">
        <el-radio-button label="image">
          <el-icon><Picture /></el-icon>
          图片检测
        </el-radio-button>
        <el-radio-button label="video">
          <el-icon><VideoPlay /></el-icon>
          视频检测
        </el-radio-button>
        <el-radio-button label="camera">
          <el-icon><Camera /></el-icon>
          摄像头检测
        </el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- 检测场景选择：用于控制 AI 回答角色 -->
    <el-card class="scenario-selector" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>检测场景选择</span>
          <el-tag type="primary" effect="plain">{{ getScenarioLabel(selectedScenario) }}</el-tag>
        </div>
      </template>
      <el-radio-group v-model="selectedScenario" size="large" @change="handleScenarioChange">
        <el-radio-button
          v-for="item in scenarioOptions"
          :key="item.value"
          :label="item.value"
        >
          {{ item.label }}
        </el-radio-button>
      </el-radio-group>
      <div class="scenario-model-row">
        <span>当前场景模型</span>
        <el-select
          v-model="selectedScenarioModel"
          class="scenario-model-select"
          placeholder="请选择模型"
          :loading="scenarioModelLoading"
          @change="handleScenarioModelChange"
        >
          <el-option
            v-for="modelItem in scenarioModels"
            :key="modelItem.path"
            :label="modelItem.name"
            :value="modelItem.path"
          >
            <span>{{ modelItem.name }}</span>
            <span class="scenario-model-path">{{ modelItem.relative_path || modelItem.path }}</span>
          </el-option>
        </el-select>
      </div>
      <div class="scenario-tip">
        点击场景后系统会自动加载对应命名规则的模型；通用检测使用 models/yolov8n.pt。
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- 左侧：上传和控制区域 -->
      <el-col :span="12">
        <el-card class="upload-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{ getModeTitle() }}</span>
              <el-button
                v-if="detectionMode === 'camera' && !isCameraActive"
                type="primary"
                @click="startCamera"
                :loading="$store.state.isLoading"
              >
                启动摄像头
              </el-button>
              <el-button
                v-if="detectionMode === 'camera' && isCameraActive"
                type="danger"
                @click="stopCamera"
              >
                停止摄像头
              </el-button>
            </div>
          </template>

          <!-- 图片上传 -->
          <div v-if="detectionMode === 'image'" class="upload-section">
            <el-upload
              class="image-uploader"
              :action="uploadAction"
              :show-file-list="false"
              :before-upload="beforeImageUpload"
              :on-success="handleImageSuccess"
              :on-error="handleUploadError"
              :data="{ user_id: $store.getters.currentUser?.id }"
              drag
            >
              <div v-if="!imageUrl" class="upload-placeholder">
                <el-icon class="upload-icon"><Plus /></el-icon>
                <div class="upload-text">
                  <p>拖拽图片到此处，或<em>点击上传</em></p>
                  <p class="upload-tip">支持 JPG、PNG、GIF 格式，大小不超过 10MB</p>
                </div>
              </div>
              <img v-else :src="imageUrl" class="uploaded-image" alt="上传的图片">
            </el-upload>
          </div>

          <!-- 视频上传 -->
          <div v-if="detectionMode === 'video'" class="upload-section">
            <el-upload
              class="video-uploader"
              :action="videoUploadAction"
              :show-file-list="false"
              :before-upload="beforeVideoUpload"
              :on-success="handleVideoSuccess"
              :on-error="handleUploadError"
              :data="{ user_id: $store.getters.currentUser?.id }"
              drag
            >
              <div v-if="!videoUrl" class="upload-placeholder">
                <el-icon class="upload-icon"><VideoPlay /></el-icon>
                <div class="upload-text">
                  <p>拖拽视频到此处，或<em>点击上传</em></p>
                  <p class="upload-tip">支持 MP4、AVI、MOV 格式，大小不超过 100MB</p>
                </div>
              </div>
              <video v-else :src="videoUrl" class="uploaded-video" controls>
                您的浏览器不支持视频播放
              </video>
            </el-upload>
          </div>

          <!-- 摄像头 -->
          <div v-if="detectionMode === 'camera'" class="camera-section">
            <div class="camera-container" :class="{ 'camera-overlay-container': isCameraActive }">
              <video
                ref="cameraVideo"
                class="camera-video"
                autoplay
                muted
                v-show="isCameraActive"
              ></video>
              <canvas
                ref="cameraCanvas"
                class="camera-canvas"
                style="display: none;"
              ></canvas>

              <!-- 实时检测框叠加层 -->
              <div v-if="isCameraActive" class="camera-detection-overlay">
                <div
                  v-for="(detection, index) in realtimeDetections"
                  :key="`detection-${index}-${detection.confidence}`"
                  class="detection-box"
                  :style="getDetectionBoxStyle(detection)"
                >
                  <span class="detection-label">
                    {{ detection.class }}: {{ (detection.confidence * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>

              <div v-if="!isCameraActive" class="camera-placeholder">
                <el-icon class="camera-icon"><Camera /></el-icon>
                <p>点击上方"启动摄像头"开始实时检测</p>
              </div>
            </div>
          </div>

          <!-- 检测控制 -->
          <div class="detection-controls" v-if="detectionMode !== 'camera'">
            <el-button
              type="primary"
              size="large"
              :disabled="!canDetect"
              :loading="$store.state.isLoading"
              @click="startDetection"
            >
              <el-icon><Search /></el-icon>
              开始检测
            </el-button>
            <el-button @click="resetUpload">
              <el-icon><RefreshRight /></el-icon>
              重新上传
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：检测结果区域 -->
      <el-col :span="12">
        <el-card class="result-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>检测结果</span>
              <div class="result-stats" v-if="detectionResult.detections">
                <el-tag type="success">
                  检测到 {{ detectionResult.detections.length }} 个目标
                </el-tag>
              </div>
            </div>
          </template>

          <div class="result-content">
            <!-- 检测结果图片 -->
            <div v-if="detectionResult.result_image && detectionMode === 'image'" class="result-media">
              <img
                :src="getResultImageUrl()"
                class="result-image"
                alt="检测结果"
                @error="handleImageError"
                @click="openImagePreview(getResultImageUrl())"
              >
              <div class="image-overlay">
                <el-button type="primary" @click="openImagePreview(getResultImageUrl())">
                  <el-icon><ZoomIn /></el-icon>
                  点击放大查看
                </el-button>
              </div>
            </div>

            <!-- 检测结果视频 -->
            <div v-if="detectionResult.result_video && detectionMode === 'video'" class="result-media">
              <video
                :src="getResultVideoUrl()"
                class="result-video"
                controls
                preload="metadata"
                @error="handleVideoError"
                @loadstart="onVideoLoadStart"
                @loadeddata="onVideoLoaded"
              >
                您的浏览器不支持视频播放
              </video>
              <div class="video-overlay">
                <el-button type="primary" @click="openVideoPreview(getResultVideoUrl())">
                  <el-icon><ZoomIn /></el-icon>
                  全屏查看
                </el-button>
              </div>
            </div>

            <!-- 智能分析结果 -->
            <div v-if="detectionResult.analysis" class="analysis-panel">
              <div class="analysis-header">
                <h4>智能分析</h4>
                <el-tag :type="detectionResult.analysis.review_required ? 'warning' : 'success'">
                  {{ detectionResult.analysis.review_required ? '建议复核' : '结果可靠' }}
                </el-tag>
              </div>

              <el-row :gutter="12" class="analysis-stats">
                <el-col :span="6">
                  <div class="analysis-stat">
                    <span class="stat-value">{{ detectionResult.analysis.total_objects }}</span>
                    <span class="stat-label">目标总数</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="analysis-stat">
                    <span class="stat-value">{{ formatPercent(detectionResult.analysis.avg_confidence) }}</span>
                    <span class="stat-label">平均置信度</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="analysis-stat">
                    <span class="stat-value">{{ formatPercent(detectionResult.analysis.max_confidence) }}</span>
                    <span class="stat-label">最高置信度</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="analysis-stat">
                    <span class="stat-value">{{ detectionResult.analysis.low_confidence_count }}</span>
                    <span class="stat-label">低置信度</span>
                  </div>
                </el-col>
              </el-row>

              <div class="analysis-conclusion">
                {{ detectionResult.analysis.conclusion }}
              </div>

              <div class="ai-actions">
                <el-button
                  type="primary"
                  :loading="aiReportLoading"
                  @click="generateAiReport"
                >
                  <el-icon><Document /></el-icon>
                  生成AI报告
                </el-button>
                <el-button @click="openChatDialog">
                  <el-icon><ChatDotRound /></el-icon>
                  智能问答
                </el-button>
                <el-button @click="showApiKeyDialog = true">
                  设置API Key
                </el-button>
                <el-button
                  v-if="hasDeepseekApiKey"
                  type="danger"
                  plain
                  @click="clearDeepseekApiKey"
                >
                  清除Key
                </el-button>
              </div>

              <div v-if="aiReport" class="ai-report">
                <div class="ai-report-title">AI自然语言报告</div>
                <div class="ai-report-content">{{ aiReport }}</div>
              </div>

              <div v-if="detectionResult.analysis.detection_type === 'video'" class="video-analysis-details">
                <div class="video-metric">
                  <span class="video-metric-value">{{ detectionResult.analysis.processed_frames }}</span>
                  <span class="video-metric-label">处理帧数</span>
                </div>
                <div class="video-metric">
                  <span class="video-metric-value">{{ detectionResult.analysis.sampled_frame_count }}</span>
                  <span class="video-metric-label">采样帧数</span>
                </div>
                <div class="video-metric">
                  <span class="video-metric-value">{{ detectionResult.analysis.detected_frame_count }}</span>
                  <span class="video-metric-label">有目标帧数</span>
                </div>
                <div class="video-metric">
                  <span class="video-metric-value">{{ formatNumber(detectionResult.analysis.avg_detections_per_sampled_frame) }}</span>
                  <span class="video-metric-label">平均目标/采样帧</span>
                </div>
              </div>

              <div v-if="Object.keys(detectionResult.analysis.class_counts || {}).length > 0" class="class-distribution">
                <span class="distribution-title">类别分布</span>
                <div class="class-tags">
                  <el-tag
                    v-for="(count, className) in detectionResult.analysis.class_counts"
                    :key="className"
                    type="info"
                    effect="plain"
                  >
                    {{ className }} × {{ count }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 检测结果列表 -->
            <div v-if="detectionResult.detections && detectionResult.detections.length > 0" class="detection-list">
              <h4>检测详情</h4>
              <el-table :data="detectionResult.detections" style="width: 100%" size="small" max-height="300">
                <el-table-column prop="class" label="类别" width="120" />
                <el-table-column label="置信度" width="100">
                  <template #default="scope">
                    <el-progress
                      :percentage="Math.round(scope.row.confidence * 100)"
                      :stroke-width="8"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="位置">
                  <template #default="scope">
                    <span class="bbox-info">
                      {{ formatBbox(scope.row.bbox) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="帧数" v-if="detectionMode === 'video'" width="80">
                  <template #default="scope">
                    {{ scope.row.frame || '--' }}
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 空状态 -->
            <div v-if="!detectionResult.detections && !$store.state.isLoading && detectionMode !== 'camera'" class="empty-result">
              <el-empty description="暂无检测结果">
                <el-button type="primary" @click="startDetection" v-if="canDetect">
                  开始检测
                </el-button>
              </el-empty>
            </div>

            <!-- 摄像头模式的空状态 -->
            <div v-if="detectionMode === 'camera' && !isCameraActive && !$store.state.isLoading" class="empty-result">
              <el-empty description="请启动摄像头开始实时检测" />
            </div>

            <!-- 实时检测统计 -->
            <div v-if="detectionMode === 'camera' && isCameraActive" class="realtime-stats">
              <el-statistic title="实时检测到的目标" :value="realtimeDetections.length" />
            </div>

            <!-- 加载状态 -->
            <div v-if="$store.state.isLoading" class="loading-result">
              <el-loading
                element-loading-text="正在进行AI检测分析..."
                element-loading-spinner="el-icon-loading"
                element-loading-background="rgba(0, 0, 0, 0.8)"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="showImagePreview"
      title="检测结果 - 放大查看"
      width="90%"
      top="5vh"
      destroy-on-close
      @close="closeImagePreview"
    >
      <div class="preview-container">
        <img
          v-if="previewImageUrl"
          :src="previewImageUrl"
          class="preview-image"
          alt="检测结果放大图"
          :style="{
            transform: `scale(${zoomLevel})`,
            cursor: 'grab'
          }"
          @load="onPreviewImageLoad"
          @error="onPreviewImageError"
          @mousedown="startDrag"
          @mousemove="drag"
          @mouseup="endDrag"
          @wheel="handleWheel"
        >
        <div class="preview-controls">
          <el-button-group>
            <el-button @click="zoomIn">
              <el-icon><ZoomIn /></el-icon>
              放大
            </el-button>
            <el-button @click="zoomOut">
              <el-icon><ZoomOut /></el-icon>
              缩小
            </el-button>
            <el-button @click="resetZoom">
              <el-icon><RefreshRight /></el-icon>
              重置
            </el-button>
            <el-button @click="downloadImage">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </el-button-group>
          <div class="zoom-info">
            缩放: {{ Math.round(zoomLevel * 100) }}%
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 视频预览对话框 -->
    <el-dialog
      v-model="showVideoPreview"
      title="检测结果 - 全屏查看"
      width="90%"
      top="5vh"
      destroy-on-close
      @close="closeVideoPreview"
    >
      <div class="preview-container">
        <video
          v-if="previewVideoUrl"
          :src="previewVideoUrl"
          class="preview-video"
          controls
          autoplay
        >
          您的浏览器不支持视频播放
        </video>
        <div class="preview-controls">
          <el-button @click="downloadVideo">
            <el-icon><Download /></el-icon>
            下载视频
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 智能问答对话框 -->
    <el-dialog
      v-model="showChatDialog"
      title="检测结果智能问答"
      width="680px"
      destroy-on-close
    >
      <div class="chat-panel">
        <div class="chat-messages" ref="chatMessagesBox">
          <div
            v-for="(message, index) in chatMessages"
            :key="index"
            class="chat-message"
            :class="message.role"
          >
            <div class="chat-bubble">{{ message.content }}</div>
          </div>
          <div v-if="chatLoading" class="chat-message assistant">
            <div class="chat-bubble">正在分析当前检测结果...</div>
          </div>
        </div>

        <div class="chat-input-row">
          <el-input
            v-model="chatInput"
            type="textarea"
            :rows="2"
            placeholder="例如：这次检测结果可靠吗？为什么建议复核？"
            @keyup.enter.exact.prevent="sendChatMessage"
          />
          <el-button
            type="primary"
            :loading="chatLoading"
            @click="sendChatMessage"
          >
            发送
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- API Key设置对话框 -->
    <el-dialog
      v-model="showApiKeyDialog"
      title="设置 DeepSeek API Key"
      width="520px"
    >
      <el-alert
        title="API Key 只会临时保存在当前浏览器会话中，关闭浏览器后失效，不会写入代码。"
        type="info"
        show-icon
        :closable="false"
        class="api-key-alert"
      />
      <el-input
        v-model="deepseekApiKeyInput"
        type="password"
        placeholder="请输入 DeepSeek API Key"
        show-password
        clearable
      />
      <template #footer>
        <el-button @click="showApiKeyDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDeepseekApiKey">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import {
  Picture,
  VideoPlay,
  Camera,
  Plus,
  Search,
  RefreshRight,
  ZoomIn,
  ZoomOut,
  Download,
  Document,
  ChatDotRound
} from '@element-plus/icons-vue'

export default {
  name: 'Detection',
  components: {
    Picture,
    VideoPlay,
    Camera,
    Plus,
    Search,
    RefreshRight,
    ZoomIn,
    ZoomOut,
    Download,
    Document,
    ChatDotRound
  },
  data() {
    return {
      detectionMode: 'image',
      selectedScenario: 'general',
      scenarioOptions: [
        { value: 'general', label: '通用检测' },
        { value: 'drone', label: '无人机检测' },
        { value: 'fire', label: '火灾检测' },
        { value: 'flower', label: '花卉检测' },
        { value: 'pest', label: '病虫害检测' }
      ],
      scenarioModels: [],
      selectedScenarioModel: '',
      scenarioModelLoading: false,
      imageUrl: '',
      videoUrl: '',
      isCameraActive: false,
      detectionResult: {},
      realtimeDetections: [],
      cameraStream: null,
      detectionInterval: null,
      uploadAction: '/api/detect_image',
      videoUploadAction: '/api/detect_video',
      videoLoading: false,
      showImagePreview: false,
      showVideoPreview: false,
      previewImageUrl: '',
      previewVideoUrl: '',
      aiReport: '',
      aiReportLoading: false,
      showChatDialog: false,
      chatMessages: [],
      chatInput: '',
      chatLoading: false,
      showApiKeyDialog: false,
      deepseekApiKeyInput: '',
      hasDeepseekApiKey: false,
      zoomLevel: 1,
      imageWidth: 0,
      imageHeight: 0,
      isDragging: false,
      dragStartX: 0,
      dragStartY: 0
    }
  },
  computed: {
    canDetect() {
      return (this.detectionMode === 'image' && this.imageUrl) ||
             (this.detectionMode === 'video' && this.videoUrl)
    }
  },
  mounted() {
    this.hasDeepseekApiKey = !!sessionStorage.getItem('deepseek_api_key')
    this.handleScenarioChange()
  },
  methods: {
    getModeTitle() {
      const titles = {
        image: '图片上传检测',
        video: '视频上传检测',
        camera: '摄像头实时检测'
      }
      return titles[this.detectionMode]
    },

    handleModeChange() {
      // 静默关闭摄像头，不显示提示
      this.silentStopCamera()
      this.resetUpload()
      this.detectionResult = {}
      this.resetAiAssistant()
    },

    async handleScenarioChange() {
      this.resetAiAssistant()
      await this.loadScenarioModels()
    },

    async loadScenarioModels() {
      this.scenarioModelLoading = true
      try {
        const listResponse = await fetch(`/api/models/scenario/${this.selectedScenario}`)
        const listData = await listResponse.json()
        if (!listData.success) {
          this.scenarioModels = []
          this.selectedScenarioModel = ''
          ElMessage.warning(listData.message || '未找到对应场景模型')
          return
        }
        this.scenarioModels = listData.models || []
        this.selectedScenarioModel = this.scenarioModels[0]?.path || ''
        if (!this.selectedScenarioModel) {
          ElMessage.warning('未找到对应场景模型，请先上传模型')
          return
        }
        await this.loadSelectedScenarioModel()
      } catch (error) {
        ElMessage.error('场景模型列表加载失败: ' + error.message)
      } finally {
        this.scenarioModelLoading = false
      }
    },

    async handleScenarioModelChange() {
      this.resetAiAssistant()
      await this.loadSelectedScenarioModel()
    },

    async loadSelectedScenarioModel() {
      if (!this.selectedScenarioModel) return
      try {
        const response = await fetch('/api/models/load_by_scenario', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            scenario: this.selectedScenario,
            model_path: this.selectedScenarioModel
          })
        })
        const data = await response.json()
        if (data.success) {
          ElMessage.success(data.message || `已切换为：${this.getScenarioLabel(this.selectedScenario)}`)
        } else {
          ElMessage.warning(data.message || '未找到对应场景模型，请先上传模型')
        }
      } catch (error) {
        ElMessage.error('场景模型切换失败: ' + error.message)
      }
    },

    getScenarioLabel(value) {
      const item = this.scenarioOptions.find(option => option.value === value)
      return item ? item.label : '通用检测'
    },

    // 图片上传相关
    beforeImageUpload(file) {
      const isImage = file.type.startsWith('image/')
      const isLt10M = file.size / 1024 / 1024 < 10

      if (!isImage) {
        ElMessage.error('只能上传图片文件!')
        return false
      }
      if (!isLt10M) {
        ElMessage.error('图片大小不能超过 10MB!')
        return false
      }

      // 保存图片URL用于预览
      this.imageUrl = URL.createObjectURL(file)
      return true
    },

    handleImageSuccess(response) {
      if (response.success) {
        // 确保结果稳定显示
        this.detectionResult = { ...response }
        this.resetAiAssistant()
        ElMessage.success('图片检测完成')
      } else {
        ElMessage.error(response.message)
      }
    },

    // 视频上传相关
    beforeVideoUpload(file) {
      const isVideo = file.type.startsWith('video/')
      const isLt100M = file.size / 1024 / 1024 < 100

      if (!isVideo) {
        ElMessage.error('只能上传视频文件!')
        return false
      }
      if (!isLt100M) {
        ElMessage.error('视频大小不能超过 100MB!')
        return false
      }

      // 保存视频URL用于预览
      this.videoUrl = URL.createObjectURL(file)
      return true
    },

    handleVideoSuccess(response) {
      if (response.success) {
        // 确保结果稳定显示
        this.detectionResult = { ...response }
        this.resetAiAssistant()
        ElMessage.success(`视频检测完成！处理了 ${response.processed_frames || 0} 帧，检测到 ${response.total_detections || 0} 个目标`)
      } else {
        ElMessage.error(response.message)
      }
    },

    handleUploadError(error, file, fileList) {
      console.error('上传错误详情:', error)
      if (error.response) {
        const errorData = error.response.data
        if (errorData && errorData.message) {
          ElMessage.error(`上传失败: ${errorData.message}`)
        } else {
          ElMessage.error(`上传失败: HTTP ${error.response.status}`)
        }
      } else {
        ElMessage.error('上传失败: ' + error.message)
      }
    },

    // 视频加载事件
    onVideoLoadStart() {
      this.videoLoading = true
      console.log('视频开始加载...')
    },

    onVideoLoaded() {
      this.videoLoading = false
      console.log('视频加载完成')
    },

    handleImageError(event) {
      console.error('图片加载错误:', event)
      ElMessage.error('图片加载失败，请检查网络连接')
    },

    handleVideoError(event) {
      console.error('视频加载错误:', event)
      const video = event.target
      let errorMessage = '视频加载失败'

      if (video.error) {
        switch (video.error.code) {
          case 1: // MEDIA_ERR_ABORTED
            errorMessage = '视频加载被中止'
            break
          case 2: // MEDIA_ERR_NETWORK
            errorMessage = '视频网络加载错误'
            break
          case 3: // MEDIA_ERR_DECODE
            errorMessage = '视频解码错误，格式可能不支持'
            break
          case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
            errorMessage = '视频格式不支持或文件损坏'
            break
          default:
            errorMessage = '视频播放出现未知错误'
        }
      }

      ElMessage.error(errorMessage)

      // 提供解决建议
      this.$notify({
        title: '视频加载失败',
        message: '建议：1. 检查网络连接 2. 尝试其他视频格式 3. 重新上传视频',
        type: 'warning',
        duration: 8000
      })
    },

    // 摄像头相关
    async startCamera() {
      try {
        this.cameraStream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          }
        })

        if (this.$refs.cameraVideo) {
          this.$refs.cameraVideo.srcObject = this.cameraStream
          this.isCameraActive = true

          // 等待视频加载后开始检测
          this.$refs.cameraVideo.onloadedmetadata = () => {
            this.startRealtimeDetection()
          }

          ElMessage.success('摄像头已启动')
        }
      } catch (error) {
        ElMessage.error('无法访问摄像头: ' + error.message)
      }
    },

    stopCamera() {
      this.silentStopCamera()
      ElMessage.success('摄像头已关闭')
    },

    silentStopCamera() {
      if (this.cameraStream) {
        this.cameraStream.getTracks().forEach(track => track.stop())
        this.cameraStream = null
      }
      if (this.detectionInterval) {
        clearInterval(this.detectionInterval)
        this.detectionInterval = null
      }
      this.isCameraActive = false
      this.realtimeDetections = []
    },

    startRealtimeDetection() {
      if (this.detectionInterval) {
        clearInterval(this.detectionInterval)
      }

      this.detectionInterval = setInterval(async () => {
        if (this.isCameraActive && this.$refs.cameraVideo && this.$refs.cameraVideo.readyState === 4) {
          const canvas = this.$refs.cameraCanvas
          const video = this.$refs.cameraVideo
          const ctx = canvas.getContext('2d')

          canvas.width = video.videoWidth
          canvas.height = video.videoHeight

          if (canvas.width > 0 && canvas.height > 0) {
            ctx.drawImage(video, 0, 0)
            const imageData = canvas.toDataURL('image/jpeg', 0.8)

            try {
              const result = await this.$store.dispatch('processFrame', imageData)
              if (result.success) {
                // 使用Vue的响应式更新，避免闪烁
                this.$nextTick(() => {
                  this.realtimeDetections = [...result.detections]
                })
              }
            } catch (error) {
              console.error('实时检测失败:', error)
            }
          }
        }
      }, 1000) // 降低检测频率到1秒，减少闪烁
    },

    // 检测相关
    async startDetection() {
      if (this.detectionMode === 'image' && this.imageUrl) {
        ElMessage.info('请重新上传图片以触发检测')
      } else if (this.detectionMode === 'video' && this.videoUrl) {
        ElMessage.info('请重新上传视频以触发检测')
      }
    },

    resetUpload() {
      // 清理旧的URL
      if (this.imageUrl && this.imageUrl.startsWith('blob:')) {
        URL.revokeObjectURL(this.imageUrl)
      }
      if (this.videoUrl && this.videoUrl.startsWith('blob:')) {
        URL.revokeObjectURL(this.videoUrl)
      }

      this.imageUrl = ''
      this.videoUrl = ''
      this.detectionResult = {}
      this.resetAiAssistant()
    },

    resetAll() {
      this.resetUpload()
      this.silentStopCamera()
    },

    // 结果显示相关
    getResultImageUrl() {
      return this.detectionResult.result_image
    },

    getResultVideoUrl() {
      return this.detectionResult.result_video
    },

    formatBbox(bbox) {
      if (!bbox || bbox.length !== 4) return ''
      return `(${Math.round(bbox[0])}, ${Math.round(bbox[1])}) - (${Math.round(bbox[2])}, ${Math.round(bbox[3])})`
    },

    formatPercent(value) {
      return `${Math.round((value || 0) * 100)}%`
    },

    formatNumber(value) {
      return Number(value || 0).toFixed(2)
    },

    getDeepseekApiKey() {
      return sessionStorage.getItem('deepseek_api_key') || ''
    },

    ensureDeepseekApiKey() {
      if (this.getDeepseekApiKey()) {
        return true
      }
      this.deepseekApiKeyInput = ''
      this.showApiKeyDialog = true
      ElMessage.info('请先设置 DeepSeek API Key')
      return false
    },

    saveDeepseekApiKey() {
      const apiKey = this.deepseekApiKeyInput.trim()
      if (!apiKey) {
        ElMessage.warning('请输入 DeepSeek API Key')
        return
      }
      sessionStorage.setItem('deepseek_api_key', apiKey)
      this.hasDeepseekApiKey = true
      this.deepseekApiKeyInput = ''
      this.showApiKeyDialog = false
      ElMessage.success('API Key 已保存到当前浏览器会话')
    },

    clearDeepseekApiKey() {
      sessionStorage.removeItem('deepseek_api_key')
      this.hasDeepseekApiKey = false
      this.deepseekApiKeyInput = ''
      ElMessage.success('API Key 已清除')
    },

    resetAiAssistant() {
      this.aiReport = ''
      this.chatMessages = []
      this.chatInput = ''
    },

    async generateAiReport() {
      if (!this.detectionResult.analysis) {
        ElMessage.warning('请先完成检测')
        return
      }
      if (!this.ensureDeepseekApiKey()) return

      this.aiReportLoading = true
      try {
        const response = await fetch('/api/analysis/report', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            analysis: this.detectionResult.analysis,
            detections: this.detectionResult.detections || [],
            detection_type: this.detectionMode,
            scenario: this.selectedScenario,
            api_key: this.getDeepseekApiKey()
          })
        })
        const data = await response.json()

        if (data.success) {
          this.aiReport = data.report
          if (data.ai_enabled) {
            ElMessage.success('AI报告生成成功')
          } else {
            ElMessage.warning(data.message || '已生成本地基础报告')
          }
        } else {
          ElMessage.error(data.message)
        }
      } catch (error) {
        ElMessage.error('AI报告生成失败: ' + error.message)
      } finally {
        this.aiReportLoading = false
      }
    },

    openChatDialog() {
      if (!this.detectionResult.analysis) {
        ElMessage.warning('请先完成检测')
        return
      }
      if (!this.ensureDeepseekApiKey()) return

      if (this.chatMessages.length === 0) {
        this.chatMessages.push({
          role: 'assistant',
          content: '你好，我可以根据当前检测结果回答问题，比如检测是否可靠、为什么建议复核、主要目标是什么。'
        })
      }
      this.showChatDialog = true
    },

    async sendChatMessage() {
      const content = this.chatInput.trim()
      if (!content || this.chatLoading) return

      this.chatMessages.push({ role: 'user', content })
      this.chatInput = ''
      this.chatLoading = true

      try {
        const response = await fetch('/api/analysis/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: content,
            messages: this.chatMessages.slice(0, -1).filter(item => item.role === 'user' || item.role === 'assistant'),
            analysis: this.detectionResult.analysis,
            detections: this.detectionResult.detections || [],
            scenario: this.selectedScenario,
            api_key: this.getDeepseekApiKey()
          })
        })
        const data = await response.json()

        if (data.success) {
          this.chatMessages.push({
            role: 'assistant',
            content: data.reply
          })
          if (!data.ai_enabled) {
            ElMessage.warning(data.message || '当前返回的是本地基础回答')
          }
        } else {
          ElMessage.error(data.message)
        }
      } catch (error) {
        ElMessage.error('智能问答失败: ' + error.message)
      } finally {
        this.chatLoading = false
        this.$nextTick(() => {
          const box = this.$refs.chatMessagesBox
          if (box) box.scrollTop = box.scrollHeight
        })
      }
    },

    getDetectionBoxStyle(detection) {
      if (!detection.bbox || !this.$refs.cameraVideo) return {}

      const video = this.$refs.cameraVideo
      const container = video.parentElement
      const videoRect = video.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()

      const [x1, y1, x2, y2] = detection.bbox

      // 计算缩放比例
      const scaleX = videoRect.width / video.videoWidth
      const scaleY = videoRect.height / video.videoHeight

      // 计算相对于容器的位置
      const left = (videoRect.left - containerRect.left) + (x1 * scaleX)
      const top = (videoRect.top - containerRect.top) + (y1 * scaleY)
      const width = (x2 - x1) * scaleX
      const height = (y2 - y1) * scaleY

      return {
        position: 'absolute',
        left: `${left}px`,
        top: `${top}px`,
        width: `${width}px`,
        height: `${height}px`,
        border: '2px solid #00ff00',
        backgroundColor: 'rgba(0, 255, 0, 0.1)',
        pointerEvents: 'none',
        zIndex: 10
      }
    },

    openImagePreview(imageUrl) {
      this.previewImageUrl = imageUrl
      this.showImagePreview = true
    },

    openVideoPreview(videoUrl) {
      this.previewVideoUrl = videoUrl
      this.showVideoPreview = true
    },

    closeImagePreview() {
      this.showImagePreview = false
      this.previewImageUrl = ''
    },

    closeVideoPreview() {
      this.showVideoPreview = false
      this.previewVideoUrl = ''
    },

    onPreviewImageLoad() {
      const image = new Image()
      image.src = this.previewImageUrl
      image.onload = () => {
        this.imageWidth = image.width
        this.imageHeight = image.height
      }
    },

    onPreviewImageError(event) {
      console.error('图片加载错误:', event)
      ElMessage.error('图片加载失败，请检查网络连接')
    },

    zoomIn() {
      this.zoomLevel += 0.1
      if (this.zoomLevel > 3) this.zoomLevel = 3
    },

    zoomOut() {
      this.zoomLevel -= 0.1
      if (this.zoomLevel < 0.1) this.zoomLevel = 0.1
    },

    resetZoom() {
      this.zoomLevel = 1
    },

    handleWheel(event) {
      event.preventDefault()
      const delta = event.deltaY > 0 ? -0.05 : 0.05
      this.zoomLevel += delta
      if (this.zoomLevel > 3) this.zoomLevel = 3
      if (this.zoomLevel < 0.1) this.zoomLevel = 0.1
    },

    startDrag(event) {
      this.isDragging = true
      this.dragStartX = event.clientX
      this.dragStartY = event.clientY
    },

    drag(event) {
      if (!this.isDragging) return
      // 这里可以实现图片拖拽移动功能
    },

    endDrag() {
      this.isDragging = false
    },

    downloadImage() {
      if (!this.previewImageUrl) return

      const link = document.createElement('a')
      link.href = this.previewImageUrl
      link.download = `检测结果_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.jpg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      ElMessage.success('图片下载已开始')
    },

    downloadVideo() {
      if (!this.previewVideoUrl) return

      const link = document.createElement('a')
      link.href = this.previewVideoUrl
      link.download = `检测结果_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.mp4`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      ElMessage.success('视频下载已开始')
    }
  },

  beforeUnmount() {
    this.silentStopCamera()
    this.resetUpload()
  }
}
</script>

<style scoped>
.detection-container {
  max-width: 1400px;
  margin: 0 auto;
}

.mode-selector {
  margin-bottom: 20px;
}

.scenario-selector {
  margin-bottom: 20px;
}

.scenario-tip {
  margin-top: 12px;
  color: #71809d;
  font-size: 13px;
  line-height: 1.6;
}

.scenario-model-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  color: #52607d;
  font-size: 14px;
  font-weight: 800;
}

.scenario-model-select {
  width: min(520px, 100%);
}

.scenario-model-path {
  float: right;
  margin-left: 16px;
  color: #94a3b8;
  font-size: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.result-stats {
  display: flex;
  gap: 10px;
}

.upload-card, .result-card {
  min-height: 600px;
}

.upload-section {
  margin-bottom: 20px;
}

.image-uploader, .video-uploader {
  width: 100%;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 20px;
}

.upload-text {
  text-align: center;
}

.upload-text p {
  margin: 5px 0;
}

.upload-tip {
  color: #999;
  font-size: 12px;
}

.uploaded-image, .uploaded-video {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
}

.camera-section {
  margin-bottom: 20px;
}

.camera-container {
  position: relative;
  width: 100%;
  height: 300px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.camera-overlay-container {
  border-color: #409eff;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.camera-canvas {
  position: absolute;
  top: 0;
  left: 0;
  visibility: hidden;
}

.camera-placeholder {
  text-align: center;
  color: #999;
}

.camera-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.camera-detection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.detection-box {
  position: absolute;
  border: 2px solid #00ff00;
  background: rgba(0, 255, 0, 0.1);
  pointer-events: none;
}

.detection-label {
  position: absolute;
  top: -25px;
  left: 0;
  background: #00ff00;
  color: black;
  padding: 2px 6px;
  font-size: 12px;
  border-radius: 3px;
  white-space: nowrap;
  pointer-events: none;
}

.detection-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.result-content {
  position: relative;
  min-height: 400px;
}

.result-media {
  margin-bottom: 20px;
  text-align: center;
  position: relative;
}

.result-image, .result-video {
  max-width: 100%;
  max-height: 350px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.3s ease;
}

.result-image:hover, .result-video:hover {
  transform: scale(1.02);
}

.image-overlay, .video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 8px;
}

.result-media:hover .image-overlay,
.result-media:hover .video-overlay {
  opacity: 1;
}

.analysis-panel {
  margin-top: 20px;
  padding: 16px;
  background: #f8fbff;
  border: 1px solid #d9ecff;
  border-radius: 8px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.analysis-header h4 {
  margin: 0;
  color: #27304f;
}

.analysis-stats {
  margin-bottom: 14px;
}

.analysis-stat {
  min-height: 72px;
  padding: 10px 6px;
  background: white;
  border-radius: 6px;
  text-align: center;
  border: 1px solid #edf2f7;
}

.stat-value {
  display: block;
  color: #409eff;
  font-size: 20px;
  font-weight: 700;
  line-height: 26px;
}

.stat-label {
  display: block;
  margin-top: 4px;
  color: #606266;
  font-size: 12px;
}

.analysis-conclusion {
  padding: 10px 12px;
  color: #303133;
  background: white;
  border-left: 4px solid #409eff;
  border-radius: 4px;
  line-height: 1.6;
}

.ai-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.ai-report {
  margin-top: 14px;
  padding: 12px;
  background: white;
  border: 1px solid #edf2f7;
  border-radius: 6px;
}

.ai-report-title {
  margin-bottom: 8px;
  color: #27304f;
  font-weight: 600;
}

.ai-report-content {
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
}

.video-analysis-details {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.video-metric {
  min-height: 62px;
  padding: 8px 6px;
  background: white;
  border: 1px solid #edf2f7;
  border-radius: 6px;
  text-align: center;
}

.video-metric-value {
  display: block;
  color: #67c23a;
  font-size: 18px;
  font-weight: 700;
  line-height: 24px;
}

.video-metric-label {
  display: block;
  margin-top: 4px;
  color: #606266;
  font-size: 12px;
}

.class-distribution {
  margin-top: 14px;
}

.distribution-title {
  display: block;
  margin-bottom: 8px;
  color: #606266;
  font-size: 13px;
  font-weight: 600;
}

.class-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detection-list {
  margin-top: 20px;
}

.detection-list h4 {
  margin-bottom: 15px;
  color: #333;
}

.bbox-info {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chat-messages {
  height: 360px;
  padding: 12px;
  overflow-y: auto;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.chat-message {
  display: flex;
  margin-bottom: 10px;
}

.chat-message.user {
  justify-content: flex-end;
}

.chat-message.assistant {
  justify-content: flex-start;
}

.chat-bubble {
  max-width: 78%;
  padding: 10px 12px;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.chat-message.user .chat-bubble {
  color: white;
  background: #409eff;
}

.chat-message.assistant .chat-bubble {
  color: #303133;
  background: white;
  border: 1px solid #e4e7ed;
}

.chat-input-row {
  display: grid;
  grid-template-columns: 1fr 82px;
  gap: 10px;
  align-items: end;
}

.api-key-alert {
  margin-bottom: 14px;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.realtime-stats {
  text-align: center;
  margin-top: 20px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.loading-result {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-container {
  position: relative;
  width: 100%;
  height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.1s ease;
  user-select: none;
}

.preview-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

.preview-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  padding: 10px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  backdrop-filter: blur(10px);
}

.preview-controls .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.preview-controls .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.zoom-info {
  color: white;
  font-size: 12px;
  text-align: center;
  margin-top: 5px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

:deep(.el-radio-button__inner) {
  padding: 12px 20px;
}

/* ===== 页面美化增强：网站化卡片、上传区、结果区 ===== */
.detection-container {
  max-width: 1440px;
}

.mode-selector {
  margin-bottom: 24px;
}

.mode-selector :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-header {
  color: #27304f;
  font-size: 16px;
  font-weight: 900;
}

.card-header span:first-child {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.card-header span:first-child::before {
  content: '';
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: linear-gradient(135deg, #7c83f5, #7dd3fc);
  box-shadow: 0 0 0 5px rgba(124, 131, 245, .12);
}

:deep(.el-radio-group) {
  padding: 6px;
  border: 1px solid rgba(203, 213, 225, .62);
  border-radius: 18px;
  background: #f8fafc;
}

:deep(.el-radio-button__inner) {
  min-width: 126px;
  border: none !important;
  border-radius: 14px !important;
  background: transparent !important;
  color: #475569;
  font-weight: 800;
  box-shadow: none !important;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #fff;
  background: linear-gradient(135deg, #7c83f5, #7dd3fc) !important;
  box-shadow: 0 12px 24px rgba(124, 131, 245, .24) !important;
}

.upload-card, .result-card {
  min-height: 650px;
}

:deep(.el-upload-dragger) {
  height: 338px;
  border: 1.5px dashed rgba(124, 131, 245, .35);
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.88), rgba(248,250,252,.9)),
    radial-gradient(circle at center, rgba(124, 131, 245, .10), transparent 55%);
  transition: all .25s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #7c83f5;
  transform: translateY(-2px);
  box-shadow: 0 18px 40px rgba(124, 131, 245, .12);
}

.upload-icon,
.camera-icon {
  color: #7c83f5;
  font-size: 56px;
  margin-bottom: 18px;
  filter: drop-shadow(0 10px 16px rgba(124, 131, 245, .18));
}

.upload-text p:first-child {
  color: #27304f;
  font-size: 16px;
  font-weight: 900;
}

.upload-text em {
  color: #7c83f5;
  font-style: normal;
}

.upload-tip {
  margin-top: 8px !important;
  color: #64748b;
}

.uploaded-image,
.uploaded-video,
.result-image,
.result-video {
  border: 1px solid rgba(203, 213, 225, .72);
  border-radius: 20px;
  background: #020617;
  box-shadow: 0 18px 42px rgba(71, 85, 105, .14);
}

.camera-container {
  height: 338px;
  border: 1.5px dashed rgba(124, 131, 245, .35);
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.88), rgba(248,250,252,.9)),
    radial-gradient(circle at center, rgba(125, 211, 252, .10), transparent 56%);
}

.camera-overlay-container {
  border-style: solid;
  border-color: rgba(124, 131, 245, .6);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.45), 0 18px 40px rgba(124, 131, 245, .12);
}

.camera-video {
  border-radius: 20px;
}

.detection-box {
  border: 2px solid #22c55e;
  background: rgba(34, 197, 94, .12);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, .85), 0 0 22px rgba(34, 197, 94, .38);
}

.detection-label {
  top: -30px;
  border-radius: 999px;
  background: #22c55e;
  color: #052e16;
  font-weight: 900;
  box-shadow: 0 10px 20px rgba(34, 197, 94, .25);
}

.detection-controls {
  gap: 12px;
  margin-top: 24px;
}

.result-content {
  min-height: 454px;
}

.result-media {
  padding: 10px;
  border-radius: 24px;
  background: linear-gradient(180deg, #f8fafc, #fff);
  border: 1px solid rgba(226, 232, 240, .85);
}

.image-overlay,
.video-overlay {
  border-radius: 20px;
  background: rgba(71, 85, 105, .56);
  backdrop-filter: blur(4px);
}

.analysis-panel,
.ai-report-section,
.detection-list,
.no-result {
  border-radius: 20px !important;
}

.analysis-panel {
  padding: 18px;
  border: 1px solid rgba(124, 131, 245, .18);
  background: linear-gradient(180deg, rgba(239, 246, 255, .9), rgba(255, 255, 255, .95));
  box-shadow: 0 14px 34px rgba(124, 131, 245, .08);
}

.analysis-stat {
  border: 1px solid rgba(226, 232, 240, .9);
  border-radius: 16px;
  box-shadow: 0 8px 18px rgba(71, 85, 105, .04);
}

.stat-value {
  color: #7c83f5;
  font-size: 22px;
}

.analysis-conclusion {
  border-left: none;
  border-radius: 16px;
  background: #fff;
  box-shadow: inset 4px 0 0 #7c83f5, 0 8px 20px rgba(71, 85, 105, .04);
}

@media (max-width: 1180px) {
  :deep(.el-col-12) {
    max-width: 100%;
    flex: 0 0 100%;
  }
  .result-card {
    margin-top: 22px;
  }
}

</style>
