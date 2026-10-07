<template>
  <div class="page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">OVERVIEW</span>
        <h1>工作概览</h1>
        <p>{{ today }} · {{ store.state.user?.username }} 的工作空间</p>
      </div>
      <el-button type="primary" @click="router.push('/dashboard/detection')"
        ><el-icon><Plus /></el-icon><span>新建检测</span></el-button
      >
    </div>
    <el-alert v-if="error" :title="error" type="warning" show-icon :closable="false" />
    <div class="metric-strip" v-loading="loading">
      <div class="metric">
        <span class="metric-label">累计检测任务</span
        ><strong class="metric-value">{{ history.length }}</strong
        ><span class="metric-detail"
          >{{ history.filter((r) => r.detection_type === 'image').length }} 图片 /
          {{ history.filter((r) => r.detection_type === 'video').length }} 视频</span
        >
      </div>
      <div class="metric">
        <span class="metric-label">累计目标次数</span
        ><strong class="metric-value">{{ totalObjects.toLocaleString() }}</strong
        ><small>含视频采样帧中的重复目标</small>
      </div>
      <div class="metric">
        <span class="metric-label">可用模型</span
        ><strong class="metric-value">{{ models.length }}</strong
        ><span class="metric-detail">{{ availableScenes }} 个场景</span>
      </div>
      <div class="metric">
        <span class="metric-label">待复核任务</span
        ><strong class="metric-value attention">{{ reviewCount }}</strong
        ><small>无目标或含低置信度结果</small>
      </div>
    </div>
    <section class="scene-section">
      <div class="section-head">
        <h2>检测场景</h2>
        <router-link to="/dashboard/models" class="subtle-link"
          >管理模型 <el-icon><ArrowRight /></el-icon
        ></router-link>
      </div>
      <div class="scene-grid">
        <button
          v-for="item in sceneData"
          :key="item.value"
          class="scene-tile"
          @click="router.push({ path: '/dashboard/detection', query: { scene: item.value } })"
        >
          <span class="scene-symbol" :style="{ color: item.color, background: item.color + '12' }"
            ><el-icon><component :is="item.icon" /></el-icon
          ></span>
          <h3>{{ item.label }}</h3>
          <span class="scene-count">{{
            item.count ? `${item.count} 个模型可用` : '待添加模型'
          }}</span
          ><el-icon class="scene-arrow"><TopRight /></el-icon>
        </button>
      </div>
    </section>
    <div class="overview-columns">
      <section class="recent-section">
        <div class="section-head">
          <h2>最近检测</h2>
          <router-link to="/dashboard/history" class="subtle-link"
            >全部记录 <el-icon><ArrowRight /></el-icon
          ></router-link>
        </div>
        <div class="table-shell">
          <el-table :data="history.slice(0, 6)" empty-text="还没有检测记录"
            ><el-table-column label="检测文件" min-width="200"
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
                    ><small>{{ formatTime(row.created_at) }}</small>
                  </div>
                </div></template
              ></el-table-column
            ><el-table-column label="目标" width="65"
              ><template #default="{ row }">{{
                row.detections?.length || 0
              }}</template></el-table-column
            ><el-table-column label="最高置信度" width="100"
              ><template #default="{ row }">{{
                percent(row.confidence)
              }}</template></el-table-column
            ><el-table-column width="54"
              ><template #default="{ row }"
                ><button
                  class="icon-button"
                  title="查看记录"
                  aria-label="查看记录"
                  @click="router.push({ path: '/dashboard/history', query: { id: row.id } })"
                >
                  <el-icon><ArrowRight /></el-icon></button></template></el-table-column
          ></el-table>
        </div>
      </section>
      <section class="distribution">
        <div class="section-head">
          <h2>目标分布</h2>
          <small>TOP 5</small>
        </div>
        <div v-if="!topClasses.length" class="empty-state">
          <el-icon><Histogram /></el-icon><strong>暂无统计</strong>
        </div>
        <div v-for="([label, count], i) in topClasses" :key="label" class="distribution-row">
          <div>
            <span>{{ label }}</span
            ><strong>{{ count }}</strong>
          </div>
          <div class="distribution-track">
            <span
              :style="{ width: `${(count / topClasses[0][1]) * 100}%`, background: barColors[i] }"
            ></span>
          </div>
        </div>
        <div class="distribution-footer"><i class="status-dot"></i> 按当前账号历史记录统计</div>
      </section>
    </div>
    <section v-if="recentImages.length" class="recent-media">
      <div class="section-head">
        <h2>结果快照</h2>
        <small>最近图片检测</small>
      </div>
      <div class="snapshot-grid">
        <button
          v-for="record in recentImages"
          :key="record.id"
          class="snapshot"
          @click="router.push({ path: '/dashboard/history', query: { id: record.id } })"
        >
          <img
            :src="`/static/${record.result_file}`"
            alt="历史检测结果"
            loading="lazy"
            @error="$event.target.style.visibility = 'hidden'"
          /><span
            ><strong>#{{ record.id }}</strong
            >{{ record.detections?.length || 0 }} 个目标<el-icon><TopRight /></el-icon
          ></span>
        </button>
      </div>
    </section>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { api, scenes, modelScenes, percent, formatTime } from '../lib/workspace'
const router = useRouter(),
  store = useStore(),
  history = ref([]),
  models = ref([]),
  loading = ref(true),
  error = ref('')
const today = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
})
const barColors = ['#438468', '#7ca794', '#c39564', '#929fae', '#b49bab']
const sceneData = computed(() =>
  scenes.map((s) => ({
    ...s,
    count: models.value.filter((m) => modelScenes(m).some((ms) => ms.value === s.value)).length,
  }))
)
const availableScenes = computed(() => sceneData.value.filter((s) => s.count).length)
const totalObjects = computed(() =>
  history.value.reduce((total, r) => total + (r.detections?.length || 0), 0)
)
const reviewCount = computed(
  () =>
    history.value.filter(
      (r) => !r.detections?.length || r.detections.some((d) => d.confidence < 0.6)
    ).length
)
const topClasses = computed(() => {
  const counts = {}
  history.value.forEach((r) =>
    r.detections?.forEach((d) => {
      counts[d.class] = (counts[d.class] || 0) + 1
    })
  )
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
})
const recentImages = computed(() =>
  history.value.filter((r) => r.detection_type === 'image' && r.result_file).slice(0, 4)
)
onMounted(async () => {
  const results = await Promise.allSettled([api(`/history/${store.state.user.id}`), api('/models')])
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') {
      if (i === 0) history.value = r.value.history
      else models.value = r.value.models
    } else error.value = r.reason.message
  })
  loading.value = false
})
</script>
<style scoped>
.attention {
  color: #ad813b;
}
.metric small {
  font-size: 10px;
}
.subtle-link {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #728279;
}
.scene-section {
  margin: 28px 0 32px;
}
.scene-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}
.scene-tile {
  position: relative;
  text-align: left;
  padding: 20px;
  background: white;
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--ink);
  transition: border-color 0.15s;
}
.scene-tile:hover {
  border-color: #92b89d;
}
.scene-symbol {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 6px;
  font-size: 21px;
  margin-bottom: 15px;
}
.scene-tile h3 {
  font-size: 13px;
  margin-bottom: 4px;
}
.scene-count {
  font-size: 10px;
  color: #95a097;
}
.scene-arrow {
  position: absolute;
  top: 22px;
  right: 16px;
  font-size: 12px;
  color: #a4b1a8;
}
.overview-columns {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(225px, 1fr);
  gap: 30px;
}
.recent-section {
  min-width: 0;
}
.distribution {
  border-left: 1px solid var(--line);
  padding-left: 25px;
}
.distribution-row {
  margin-bottom: 22px;
}
.distribution-row > div:first-child {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  margin-bottom: 9px;
}
.distribution-row strong {
  font-weight: 500;
  color: #859188;
}
.distribution-track {
  background: #e9eeea;
  height: 6px;
  border-radius: 2px;
  overflow: hidden;
}
.distribution-track span {
  display: block;
  height: 100%;
  border-radius: 2px;
}
.distribution-footer {
  font-size: 10px;
  color: #99a39b;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 28px;
}
.recent-media {
  margin-top: 30px;
}
.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}
.snapshot {
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
  background: white;
  text-align: left;
}
.snapshot img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: contain;
  background: #e8eee9;
}
.snapshot > span {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  font-size: 10px;
  color: #88978c;
}
.snapshot strong {
  color: #536f5c;
  font-weight: 500;
}
.snapshot .el-icon {
  margin-left: auto;
}
@media (max-width: 1050px) {
  .scene-tile {
    padding: 14px;
  }
  .scene-arrow {
    display: none;
  }
  .overview-columns {
    grid-template-columns: 1fr;
  }
  .distribution {
    border: 0;
    padding: 0;
  }
}
@media (max-width: 760px) {
  .scene-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .snapshot-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
