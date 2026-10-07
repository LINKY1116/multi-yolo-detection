<template>
  <div class="page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">DETECTION ARCHIVE</span>
        <h1>检测记录</h1>
        <p>已保存的图片与视频检测任务</p>
      </div>
      <div class="actions">
        <el-button :disabled="!filtered.length" @click="exportRecords(filtered)"
          ><el-icon><Download /></el-icon><span>导出 CSV</span></el-button
        ><el-button :loading="loading" @click="refresh"
          ><el-icon><Refresh /></el-icon><span>刷新</span></el-button
        >
      </div>
    </div>
    <el-alert v-if="error" :title="error" type="error" show-icon @close="error = ''" />
    <div class="metric-strip">
      <div class="metric">
        <span class="metric-label">全部记录</span
        ><strong class="metric-value">{{ records.length }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">图片检测</span
        ><strong class="metric-value">{{
          records.filter((r) => r.detection_type === 'image').length
        }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">视频检测</span
        ><strong class="metric-value">{{
          records.filter((r) => r.detection_type === 'video').length
        }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">待复核记录</span
        ><strong class="metric-value" style="color: #ad813b">{{
          records.filter(needsReview).length
        }}</strong>
      </div>
    </div>
    <div class="toolbar">
      <el-input
        v-model="search"
        clearable
        placeholder="搜索文件名、类别或记录 ID"
        aria-label="搜索检测记录"
        ><template #prefix
          ><el-icon><Search /></el-icon></template></el-input
      ><el-select v-model="type" aria-label="检测类型"
        ><el-option label="全部类型" value="" /><el-option label="图片" value="image" /><el-option
          label="视频"
          value="video" /><el-option label="摄像头" value="camera" /></el-select
      ><el-date-picker
        v-model="dates"
        type="daterange"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        range-separator="至"
        :editable="false"
      /><el-checkbox v-model="onlyReview">仅待复核</el-checkbox
      ><el-button v-if="hasFilters" text @click="resetFilters">重置</el-button>
    </div>
    <div class="selection-bar">
      <span>{{
        selection.length ? `已选择 ${selection.length} 条` : `共 ${filtered.length} 条结果`
      }}</span>
      <div class="actions">
        <el-button
          size="small"
          type="danger"
          plain
          :disabled="!selection.length || deleting"
          @click="removeSelected"
          ><el-icon><Delete /></el-icon><span>删除选中</span></el-button
        ><el-button
          size="small"
          text
          type="danger"
          :disabled="!records.length || deleting"
          @click="clearAll"
          >清空全部</el-button
        >
      </div>
    </div>
    <div class="table-shell" v-loading="loading || deleting">
      <el-table ref="table" :data="pageRows" row-key="id" @selection-change="selection = $event"
        ><el-table-column type="selection" width="43" /><el-table-column
          label="检测文件"
          min-width="240"
          ><template #default="{ row }"
            ><div class="file-cell">
              <span class="file-icon"
                ><el-icon
                  ><component
                    :is="row.detection_type === 'video' ? 'VideoPlay' : 'Picture'" /></el-icon
              ></span>
              <div class="file-info">
                <span class="file-name" :title="row.original_file">{{
                  row.original_file || '实时检测'
                }}</span
                ><small>#{{ row.id }} · {{ typeLabel(row.detection_type) }}</small>
              </div>
            </div></template
          ></el-table-column
        ><el-table-column label="检测时间" min-width="170"
          ><template #default="{ row }"
            ><span class="time-label">{{ formatTime(row.created_at) }}</span></template
          ></el-table-column
        ><el-table-column label="目标次数" width="90"
          ><template #default="{ row }">{{
            row.detections?.length || 0
          }}</template></el-table-column
        ><el-table-column label="最高置信度" width="110"
          ><template #default="{ row }">{{ percent(row.confidence) }}</template></el-table-column
        ><el-table-column label="状态" width="100"
          ><template #default="{ row }"
            ><el-tag size="small" effect="plain" :type="needsReview(row) ? 'warning' : 'success'">{{
              needsReview(row) ? '待复核' : '已完成'
            }}</el-tag></template
          ></el-table-column
        ><el-table-column label="操作" width="128" fixed="right"
          ><template #default="{ row }"
            ><div class="row-actions">
              <button
                class="icon-button"
                aria-label="查看详情"
                title="查看详情"
                @click="detail = row"
              >
                <el-icon><View /></el-icon></button
              ><a
                v-if="row.result_file"
                class="icon-button"
                :href="`/static/${row.result_file}`"
                :download="row.result_file"
                aria-label="下载结果"
                title="下载结果"
                ><el-icon><Download /></el-icon></a
              ><button
                class="icon-button"
                aria-label="删除记录"
                title="删除记录"
                :disabled="deleting"
                @click="removeRecord(row)"
              >
                <el-icon><Delete /></el-icon>
              </button></div></template></el-table-column
        ><template #empty
          ><div class="empty-state">
            <el-icon><Document /></el-icon
            ><strong>{{ hasFilters ? '没有符合条件的记录' : '还没有检测记录' }}</strong
            ><el-button v-if="hasFilters" size="small" @click="resetFilters">清除筛选</el-button
            ><el-button v-else size="small" @click="router.push('/dashboard/detection')"
              >新建检测</el-button
            >
          </div></template
        ></el-table
      >
    </div>
    <div class="pagination">
      <span>每页 {{ pageSize }} 条</span
      ><el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="filtered.length"
        layout="prev, pager, next"
        background
      />
    </div>
    <el-dialog
      :model-value="!!detail"
      @update:model-value="!$event && (detail = null)"
      title="检测详情"
      width="880px"
      ><template v-if="detail"
        ><div class="detail-meta">
          <span>#{{ detail.id }} · {{ typeLabel(detail.detection_type) }}</span
          ><span>{{ formatTime(detail.created_at) }}</span
          ><el-tag effect="plain" :type="needsReview(detail) ? 'warning' : 'success'">{{
            needsReview(detail) ? '建议人工复核' : '已完成'
          }}</el-tag>
        </div>
        <div v-if="detail.result_file" class="detail-media">
          <video
            v-if="detail.detection_type === 'video'"
            :src="`/static/${detail.result_file}`"
            controls
          /><el-image
            v-else
            :src="`/static/${detail.result_file}`"
            fit="contain"
            :preview-src-list="[`/static/${detail.result_file}`]"
            preview-teleported
            ><template #error><p>结果文件不可用</p></template></el-image
          >
        </div>
        <el-table :data="detail.detections || []" max-height="280" empty-text="未检测到目标"
          ><el-table-column prop="class" label="类别" /><el-table-column label="置信度"
            ><template #default="{ row }">{{ percent(row.confidence) }}</template></el-table-column
          ><el-table-column label="坐标" min-width="165"
            ><template #default="{ row }"
              ><span class="mono">{{ (row.bbox || []).map(Math.round).join(', ') }}</span></template
            ></el-table-column
          ></el-table
        ></template
      ><template #footer
        ><el-button @click="saveFile(JSON.stringify(detail, null, 2), `record-${detail.id}.json`)"
          >导出 JSON</el-button
        ><el-button type="primary" @click="detail = null">关闭</el-button></template
      ></el-dialog
    >
  </div>
</template>
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, percent, typeLabel, formatTime, exportRecords, saveFile } from '../lib/workspace'
const store = useStore(),
  route = useRoute(),
  router = useRouter()
const records = ref([]),
  search = ref(''),
  type = ref(''),
  dates = ref(null),
  onlyReview = ref(false),
  page = ref(1),
  pageSize = ref(10),
  selection = ref([]),
  detail = ref(null),
  loading = ref(false),
  deleting = ref(false),
  error = ref(''),
  table = ref(null)
const needsReview = (row) =>
  !row.detections?.length || row.detections.some((d) => d.confidence < 0.6)
const hasFilters = computed(
  () => !!(search.value || type.value || dates.value?.length || onlyReview.value)
)
const filtered = computed(() =>
  records.value.filter((r) => {
    const text = `${r.id} ${r.original_file || ''} ${(r.detections || [])
      .map((d) => d.class)
      .join(' ')}`.toLowerCase()
    if (search.value && !text.includes(search.value.toLowerCase())) return false
    if (type.value && r.detection_type !== type.value) return false
    if (onlyReview.value && !needsReview(r)) return false
    if (dates.value?.length) {
      const time = new Date(
        /[zZ]|[+-]\d\d:\d\d$/.test(r.created_at) ? r.created_at : `${r.created_at}Z`
      ).getTime()
      const end = new Date(dates.value[1])
      end.setHours(23, 59, 59, 999)
      if (time < dates.value[0].getTime() || time > end.getTime()) return false
    }
    return true
  })
)
const pageRows = computed(() =>
  filtered.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value)
)
watch([search, type, dates, onlyReview, pageSize], () => {
  page.value = 1
  table.value?.clearSelection()
})
watch(page, () => table.value?.clearSelection())
function resetFilters() {
  search.value = ''
  type.value = ''
  dates.value = null
  onlyReview.value = false
}
async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const data = await api(`/history/${store.state.user.id}`)
    records.value = data.history
    page.value = Math.min(
      page.value,
      Math.max(1, Math.ceil(filtered.value.length / pageSize.value))
    )
    table.value?.clearSelection()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
async function confirmDelete(message, path, data) {
  try {
    await ElMessageBox.confirm(message, '删除确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    deleting.value = true
    await api(path, { method: 'DELETE', data })
    detail.value = null
    await refresh()
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error(e.message)
  } finally {
    deleting.value = false
  }
}
function removeRecord(row) {
  confirmDelete('删除该记录及其原始文件、结果文件？此操作不可恢复。', `/history/delete/${row.id}`)
}
function removeSelected() {
  confirmDelete(
    `删除选中的 ${selection.value.length} 条记录及关联文件？`,
    '/history/batch-delete',
    { record_ids: selection.value.map((r) => r.id), user_id: store.state.user.id }
  )
}
function clearAll() {
  confirmDelete(
    `清空当前账号的全部 ${records.value.length} 条记录和关联文件？此操作不可恢复。`,
    `/history/clear/${store.state.user.id}`
  )
}
onMounted(async () => {
  await refresh()
  if (route.query.id)
    detail.value = records.value.find((r) => String(r.id) === String(route.query.id)) || null
})
</script>
<style scoped>
.selection-bar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
  font-size: 11px;
  color: #8b978e;
}
.row-actions {
  display: flex;
  gap: 5px;
}
.row-actions .icon-button {
  width: 28px;
  height: 28px;
  border: 0;
  font-size: 15px;
  background: transparent;
}
.time-label {
  color: #7d8a81;
  font-size: 12px;
}
.detail-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
  margin-bottom: 18px;
  font-size: 12px;
  color: var(--muted);
}
.detail-media {
  background: #e9efea;
  height: 320px;
  margin-bottom: 18px;
}
.detail-media > * {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.detail-media :deep(.el-image__error) {
  font-size: 12px;
}
@media (max-width: 760px) {
  .detail-media {
    height: 220px;
  }
}
</style>
