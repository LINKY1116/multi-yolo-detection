<template>
  <div class="page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">MODEL REGISTRY</span>
        <h1>模型资源</h1>
        <p>{{ models.length }} 个模型 · {{ scenes.length }} 类检测场景</p>
      </div>
      <div class="actions">
        <el-button :loading="loading" @click="refresh"
          ><el-icon><Refresh /></el-icon><span>刷新</span></el-button
        ><el-button type="primary" @click="uploadOpen = true"
          ><el-icon><Upload /></el-icon><span>上传模型</span></el-button
        >
      </div>
    </div>
    <el-alert v-if="error" :title="error" type="error" show-icon @close="error = ''" />
    <section class="active-model">
      <span class="model-chip"
        ><el-icon><Cpu /></el-icon
      ></span>
      <div>
        <span class="eyebrow">当前推理模型</span>
        <h2>{{ fileName(current.path) }}</h2>
        <span class="mono">{{ current.path || '--' }}</span>
      </div>
      <div class="active-model-end">
        <span class="status-label" :class="{ off: !current.loaded }"
          ><i class="status-dot" :class="{ off: !current.loaded }"></i
          >{{ current.loaded ? '已加载' : '未加载' }}</span
        ><span>{{ current.class_count || 0 }} 个目标类别</span
        ><el-button
          v-if="current.loaded"
          size="small"
          @click="
            detail = models.find((m) => m.path === current.path) || {
              path: current.path,
              name: fileName(current.path),
            }
          "
          >查看类别</el-button
        >
      </div>
    </section>
    <div class="toolbar">
      <el-input v-model="search" clearable placeholder="搜索模型名称" aria-label="搜索模型"
        ><template #prefix
          ><el-icon><Search /></el-icon></template></el-input
      ><el-select v-model="filterScene" aria-label="按场景筛选"
        ><el-option label="全部场景" value="" /><el-option
          v-for="s in scenes"
          :key="s.value"
          :label="s.label"
          :value="s.value" /><el-option label="未分类" value="unknown" /></el-select
      ><el-select v-model="sortBy" aria-label="模型排序"
        ><el-option label="名称排序" value="name" /><el-option
          label="最新添加"
          value="recent" /><el-option label="文件从小到大" value="size"
      /></el-select>
    </div>
    <div class="table-shell" v-loading="loading">
      <el-table :data="filtered" empty-text="没有符合条件的模型"
        ><el-table-column label="模型名称" min-width="245"
          ><template #default="{ row }"
            ><div class="file-cell">
              <span class="file-icon"
                ><el-icon><Cpu /></el-icon
              ></span>
              <div class="file-info">
                <span class="file-name" :title="row.name">{{ row.name }}</span
                ><small class="mono">{{ row.relative_path || row.path }}</small>
              </div>
            </div></template
          ></el-table-column
        ><el-table-column label="适用场景" min-width="140"
          ><template #default="{ row }"
            ><div class="tag-list">
              <el-tag
                v-for="s in modelScenes(row)"
                :key="s.value"
                size="small"
                effect="plain"
                :style="{ color: s.color }"
                >{{ s.short }}</el-tag
              ><span v-if="!modelScenes(row).length" class="muted">未分类</span>
            </div></template
          ></el-table-column
        ><el-table-column label="大小" width="100"
          ><template #default="{ row }"
            ><span class="mono">{{ row.size_mb || 0 }} MB</span></template
          ></el-table-column
        ><el-table-column label="状态" width="110"
          ><template #default="{ row }"
            ><span v-if="current.path === row.path && current.loaded" class="status-label"
              ><i class="status-dot"></i>使用中</span
            ><span v-else class="muted">{{ row.pretrained ? '待下载' : '待加载' }}</span></template
          ></el-table-column
        ><el-table-column label="操作" width="195" fixed="right"
          ><template #default="{ row }"
            ><div class="actions">
              <el-button
                size="small"
                :disabled="!!pending || row.pretrained"
                :loading="pending === row.path"
                @click="activate(row)"
                >{{ current.path === row.path && current.loaded ? '重新加载' : '加载' }}</el-button
              ><button
                class="icon-button"
                aria-label="模型详情"
                title="模型详情"
                @click="detail = row"
              >
                <el-icon><InfoFilled /></el-icon></button
              ><button
                class="icon-button"
                aria-label="删除模型"
                title="删除模型"
                :disabled="!!pending || current.path === row.path || row.pretrained"
                @click="remove(row)"
              >
                <el-icon><Delete /></el-icon>
              </button></div></template></el-table-column
      ></el-table>
    </div>
    <section class="naming-section">
      <div class="section-head">
        <h2>场景命名规则</h2>
        <span class="mono">models/</span>
      </div>
      <div class="rules-list">
        <div v-for="s in scenes" :key="s.value" class="rule-row">
          <span class="rule-label"
            ><el-icon :style="{ color: s.color }"><component :is="s.icon" /></el-icon
            >{{ s.label }}</span
          ><code>{{ s.value === 'general' ? 'yolov8n.pt / general_yolov8s.pt' : s.file }}</code
          ><span class="rule-keywords">{{ s.keywords.join(' · ') }}</span>
        </div>
      </div>
    </section>
    <el-dialog
      v-model="uploadOpen"
      destroy-on-close
      @closed="resetUpload"
      title="上传检测模型"
      width="510px"
      :close-on-click-modal="!uploading"
      :show-close="!uploading"
      :close-on-press-escape="!uploading"
      ><el-upload
        :auto-upload="false"
        :limit="1"
        accept=".pt,.onnx,.torchscript"
        :disabled="uploading"
        :on-change="selectUpload"
        :on-remove="() => (uploadFile = null)"
        :on-exceed="() => ElMessage.warning('请先移除已选文件')"
        drag
        ><el-icon class="upload-icon"><UploadFilled /></el-icon>
        <p>选择或拖入模型文件</p>
        <small>.pt / .onnx / .torchscript · 小于 100 MB</small></el-upload
      ><el-form label-position="top" class="upload-name-form"
        ><el-form-item label="保存文件名"
          ><el-input
            v-model="uploadName"
            :disabled="uploading"
            placeholder="例如 fire_yolov8s.pt" /></el-form-item
      ></el-form>
      <div v-if="uploadName" class="tag-list">
        <el-tag v-for="s in modelScenes({ name: uploadName })" :key="s.value" effect="plain">{{
          s.label
        }}</el-tag
        ><el-tag v-if="!modelScenes({ name: uploadName }).length" type="warning"
          >未匹配场景关键词</el-tag
        >
      </div>
      <el-progress v-if="uploading" :percentage="progress" :stroke-width="5" /><template #footer
        ><el-button :disabled="uploading" @click="uploadOpen = false">取消</el-button
        ><el-button type="primary" :loading="uploading" :disabled="!uploadFile" @click="upload"
          >上传</el-button
        ></template
      ></el-dialog
    >
    <el-dialog
      :model-value="!!detail"
      @update:model-value="!$event && (detail = null)"
      title="模型详情"
      width="620px"
      ><template v-if="detail"
        ><h2>{{ detail.name }}</h2>
        <p class="mono detail-path">{{ detail.path }}</p>
        <template v-if="detail.path === current.path && current.loaded"
          ><div class="section-head">
            <h3>可识别类别</h3>
            <small>{{ current.class_count }} 类</small>
          </div>
          <div class="tag-list class-list">
            <el-tag v-for="name in current.classes" :key="name" effect="plain" type="info">{{
              name
            }}</el-tag>
          </div></template
        ><el-empty v-else description="模型加载后可查看类别" :image-size="60" /></template
      ><template #footer
        ><el-button @click="detail = null">关闭</el-button
        ><el-button
          v-if="detail && detail.path !== current.path"
          type="primary"
          :loading="pending === detail.path"
          @click="activate(detail)"
          >加载模型</el-button
        ></template
      ></el-dialog
    >
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, scenes, modelScenes, fileName } from '../lib/workspace'
const models = ref([]),
  current = ref({}),
  loading = ref(false),
  error = ref(''),
  search = ref(''),
  filterScene = ref(''),
  sortBy = ref('name'),
  pending = ref(''),
  detail = ref(null)
const uploadOpen = ref(false),
  uploadFile = ref(null),
  uploadName = ref(''),
  uploading = ref(false),
  progress = ref(0)
const filtered = computed(() =>
  models.value
    .filter((m) => {
      if (!m.name.toLowerCase().includes(search.value.toLowerCase())) return false
      const matched = modelScenes(m)
      return (
        !filterScene.value ||
        (filterScene.value === 'unknown'
          ? !matched.length
          : matched.some((s) => s.value === filterScene.value))
      )
    })
    .sort((a, b) =>
      sortBy.value === 'size'
        ? a.size_mb - b.size_mb
        : sortBy.value === 'recent'
        ? b.modified - a.modified
        : a.name.localeCompare(b.name)
    )
)
async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [list, active] = await Promise.all([api('/models'), api('/models/current')])
    models.value = list.models
    current.value = active.model_info
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
async function activate(row) {
  if (pending.value) return
  pending.value = row.path
  error.value = ''
  try {
    await api('/models/load', { method: 'POST', data: { model_path: row.path } })
    await refresh()
    window.dispatchEvent(new Event('model-changed'))
    ElMessage.success('模型已加载')
  } catch (e) {
    error.value = e.message
  } finally {
    pending.value = ''
  }
}
async function remove(row) {
  try {
    await ElMessageBox.confirm(`删除 ${row.name}？此操作不可恢复。`, '删除模型', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    pending.value = row.path
    await api('/models/delete', { method: 'DELETE', data: { model_path: row.path } })
    await refresh()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') error.value = e.message
  } finally {
    pending.value = ''
  }
}
function resetUpload() {
  uploadFile.value = null
  uploadName.value = ''
  progress.value = 0
}
function selectUpload(item) {
  uploadFile.value = item.raw
  uploadName.value = item.name
}
async function upload() {
  if (!uploadFile.value || uploading.value) return
  const name = uploadName.value.trim()
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_.-]*\.(pt|onnx|torchscript)$/i.test(name)) {
    ElMessage.warning('文件名请使用英文字母、数字、下划线或短横线，并保留模型扩展名')
    return
  }
  if (
    name.split('.').pop().toLowerCase() !== uploadFile.value.name.split('.').pop().toLowerCase()
  ) {
    ElMessage.warning('不能通过修改扩展名转换模型格式')
    return
  }
  if (uploadFile.value.size >= 100 * 1048576) {
    ElMessage.warning('网页上传限制为 100 MB；更大的模型请放入 models 目录后刷新')
    return
  }
  const form = new FormData()
  form.append('file', uploadFile.value, name)
  uploading.value = true
  progress.value = 0
  try {
    await api('/models/upload', {
      method: 'POST',
      data: form,
      timeout: 0,
      onUploadProgress: (e) => {
        progress.value = e.total ? Math.round((e.loaded / e.total) * 100) : 0
      },
    })
    uploadOpen.value = false
    await refresh()
    ElMessage.success('模型已上传')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    uploading.value = false
  }
}
onMounted(refresh)
onBeforeRouteLeave(() => {
  if (pending.value || uploading.value) {
    ElMessage.info('模型操作完成后可切换页面')
    return false
  }
})
</script>
<style scoped>
.active-model {
  display: flex;
  align-items: center;
  gap: 17px;
  padding: 22px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  margin-bottom: 25px;
}
.model-chip {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 7px;
  background: #e8f0e9;
  color: #498762;
  font-size: 28px;
  flex-shrink: 0;
}
.active-model h2 {
  font-size: 18px;
  overflow-wrap: anywhere;
}
.active-model .mono {
  font-size: 10px;
  color: #9da79f;
}
.active-model-end {
  margin-left: auto;
  display: flex;
  gap: 16px;
  align-items: center;
  font-size: 12px;
  color: #8e9a91;
  flex-shrink: 0;
}
.active-model .eyebrow {
  font-size: 10px;
  margin-bottom: 3px;
}
.actions .icon-button {
  width: 28px;
  height: 28px;
  border: 0;
  background: transparent;
  font-size: 15px;
}
.icon-button:disabled {
  opacity: 0.3;
}
.naming-section {
  margin-top: 35px;
}
.naming-section h2 {
  font-size: 15px;
}
.rules-list {
  border-top: 1px solid var(--line);
}
.rule-row {
  padding: 15px 0;
  display: grid;
  grid-template-columns: 140px minmax(230px, 1fr) 1.1fr;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid var(--line);
  font-size: 12px;
}
.rule-label {
  display: flex;
  align-items: center;
  gap: 9px;
}
.rule-label .el-icon {
  font-size: 18px;
}
.rule-row code {
  font-size: 11px;
  color: #63786b;
  overflow-wrap: anywhere;
}
.rule-keywords {
  font-size: 11px;
  color: #9aa49d;
}
.upload-icon {
  font-size: 35px;
  margin-bottom: 12px;
  color: #769481;
}
.upload-name-form {
  margin-top: 20px;
}
.detail-path {
  margin: 10px 0 24px;
  color: #8d9d92;
}
.class-list {
  max-height: 350px;
  overflow-y: auto;
}
@media (max-width: 1100px) {
  .rule-row {
    grid-template-columns: 120px 1fr;
  }
  .rule-keywords {
    grid-column: 2;
  }
}
@media (max-width: 760px) {
  .active-model {
    flex-wrap: wrap;
  }
  .active-model > div {
    min-width: 0;
    flex: 1;
  }
  .active-model-end {
    flex-basis: 100% !important;
    margin: 8px 0 0;
    justify-content: space-between;
    flex-wrap: wrap;
  }
  .rule-row {
    grid-template-columns: 95px minmax(0, 1fr);
    gap: 9px;
  }
}
</style>
