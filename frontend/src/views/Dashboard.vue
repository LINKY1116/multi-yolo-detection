<template>
  <div class="workspace-shell">
    <div v-if="mobileOpen" class="nav-backdrop" @click="mobileOpen = false"></div>
    <aside class="sidebar" :class="{ 'mobile-open': mobileOpen }">
      <router-link to="/dashboard/home" class="brand" @click="mobileOpen = false"
        ><span class="brand-symbol"
          ><el-icon><Aim /></el-icon></span
        ><span>Multi YOLO<small>视觉检测工作台</small></span></router-link
      >
      <div class="nav-label">工作空间</div>
      <nav>
        <router-link
          v-for="item in navigation"
          :key="item.path"
          :to="item.path"
          @click="mobileOpen = false"
          ><el-icon><component :is="item.icon" /></el-icon><span>{{ item.label }}</span
          ><span v-if="item.path.endsWith('detection')" class="nav-hint">YOLO</span></router-link
        >
      </nav>
      <div class="sidebar-bottom">
        <button
          class="assistant-entry"
          @click="openAssistant"
        >
          <el-icon><ChatDotRound /></el-icon><span>小 Y 助手</span><el-icon><TopRight /></el-icon>
        </button>
        <div class="sidebar-model">
          <span class="status-label" :class="{ off: !loaded }"
            ><i class="status-dot" :class="{ off: !loaded }"></i
            >{{ loaded ? '推理模型已就绪' : '推理模型未就绪' }}</span
          ><span class="mono">{{ fileName(currentModel) }}</span>
        </div>
      </div>
    </aside>
    <div class="workspace-main">
      <header class="topbar">
        <div class="breadcrumb">
          <button class="icon-button mobile-menu" aria-label="打开导航" @click="mobileOpen = true">
            <el-icon><Menu /></el-icon></button
          ><span>工作空间</span><el-icon><ArrowRight /></el-icon><strong>{{ pageTitle }}</strong>
        </div>
        <div class="topbar-actions">
          <span class="status-label" :class="{ off: !online }"
            ><i class="status-dot" :class="{ off: !online }"></i
            >{{ online ? '服务已连接' : '服务未连接' }}</span
          ><span class="topbar-divider"></span
          ><el-dropdown @command="logout"
            ><button class="user-button">
              <span class="user-avatar">{{ username.slice(0, 1).toUpperCase() }}</span
              ><span>{{ username }}</span
              ><el-icon><ArrowDown /></el-icon></button
            ><template #dropdown
              ><el-dropdown-menu
                ><el-dropdown-item command="logout">退出登录</el-dropdown-item></el-dropdown-menu
              ></template
            ></el-dropdown
          >
        </div>
      </header>
      <main class="workspace-content"><router-view /></main>
      <footer class="workspace-footer">
        <span>Multi YOLO / Visual Intelligence</span><span>图片 · 视频 · 实时检测</span>
      </footer>
    </div>
    <FloatingAssistant v-model="assistantOpen" />
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { api, fileName } from '../lib/workspace'
import FloatingAssistant from '../components/FloatingAssistant.vue'
const route = useRoute(),
  router = useRouter(),
  store = useStore()
const mobileOpen = ref(false),
  assistantOpen = ref(false),
  online = ref(false),
  loaded = ref(false),
  currentModel = ref('')
const navigation = [
  { path: '/dashboard/home', icon: 'DataAnalysis', label: '工作概览' },
  { path: '/dashboard/detection', icon: 'Aim', label: '检测工作台' },
  { path: '/dashboard/history', icon: 'Clock', label: '检测记录' },
  { path: '/dashboard/models', icon: 'Cpu', label: '模型资源' },
]
const username = computed(() => store.state.user?.username || '用户')
const pageTitle = computed(
  () => navigation.find((item) => item.path === route.path)?.label || '工作空间'
)
let timer
async function check() {
  try {
    const data = await api('/models/current', { timeout: 5000 })
    online.value = true
    loaded.value = data.model_info.loaded
    currentModel.value = data.model_info.path
  } catch {
    online.value = false
    loaded.value = false
  }
}
function openAssistant() {
  assistantOpen.value = true
  mobileOpen.value = false
}
function logout() {
  store.dispatch('logout')
  router.push('/login')
}
onMounted(() => {
  store.dispatch('initializeAuth')
  check()
  timer = setInterval(check, 20000)
  window.addEventListener('model-changed', check)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  window.removeEventListener('model-changed', check)
})
</script>
<style scoped>
.workspace-shell {
  min-height: 100vh;
}
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: 218px;
  display: flex;
  flex-direction: column;
  background: #fbfcfb;
  border-right: 1px solid var(--line);
  padding: 30px 18px 18px;
  z-index: 100;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 0 5px;
  font-size: 21px;
  font-weight: 650;
  line-height: 1.3;
  white-space: nowrap;
}
.brand-symbol {
  width: 35px;
  height: 35px;
  background: #19684b;
  color: white;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 23px;
}
.brand small {
  display: block;
  margin-top: 6px;
  font-size: 10px;
  font-weight: 400;
  color: #8a938c;
}
.nav-label {
  font-size: 10px;
  color: #9aa49c;
  padding: 0 13px;
  margin: 45px 0 12px;
}
nav {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
nav a {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  color: #7b857e;
  font-size: 13px;
  border-radius: 6px;
}
nav a > .el-icon {
  font-size: 18px;
}
nav a:hover {
  background: #f1f5f1;
}
nav a.router-link-active {
  background: #eaf2eb;
  color: #19684b;
  font-weight: 600;
}
.nav-hint {
  margin-left: auto;
  font-size: 8px;
  font-weight: 500;
  border: 1px solid #d2dfd5;
  color: #779681;
  padding: 1px 3px;
  border-radius: 3px;
}
.sidebar-bottom {
  margin-top: auto;
}
.assistant-entry {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #55665a;
  background: none;
  width: 100%;
  border: 0;
  padding: 15px 12px;
  font-size: 13px;
}
.assistant-entry .el-icon:last-child {
  margin-left: auto;
  color: #8d9a91;
}
.sidebar-model {
  padding: 18px 10px 4px;
  border-top: 1px solid var(--line);
  display: grid;
  gap: 7px;
}
.sidebar-model > .mono {
  color: #9aa39d;
  font-size: 10px;
}
.workspace-main {
  margin-left: 218px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.topbar {
  height: 70px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background: #ffffffd9;
  gap: 20px;
}
.breadcrumb,
.topbar-actions {
  display: flex;
  gap: 16px;
  align-items: center;
  font-size: 12px;
}
.breadcrumb > span {
  color: #97a199;
}
.breadcrumb > .el-icon {
  font-size: 10px;
  color: #afb6b0;
}
.breadcrumb strong {
  font-weight: 500;
}
.topbar-divider {
  height: 22px;
  border-left: 1px solid var(--line);
}
.user-button {
  display: flex;
  align-items: center;
  gap: 9px;
  background: none;
  border: 0;
  color: #5c685f;
  font-size: 12px;
  max-width: 180px;
}
.user-button > span:nth-child(2) {
  max-width: 95px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-avatar {
  width: 29px;
  height: 29px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e8eee8;
  color: #51745c;
  font-size: 12px;
}
.workspace-content {
  padding: 30px 32px;
  flex: 1;
  min-width: 0;
}
.workspace-footer {
  padding: 14px 32px;
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #a4ada6;
  gap: 15px;
}
.mobile-menu {
  display: none;
}
@media (max-width: 1000px) {
  .sidebar {
    width: 190px;
    padding: 26px 12px 16px;
  }
  .workspace-main {
    margin-left: 190px;
  }
  .workspace-content {
    padding: 24px;
  }
  .brand {
    font-size: 19px;
  }
}
@media (max-width: 760px) {
  .sidebar {
    transform: translateX(-100%);
    width: 218px;
    transition: transform 0.2s;
  }
  .sidebar.mobile-open {
    transform: translateX(0);
  }
  .nav-backdrop {
    position: fixed;
    inset: 0;
    background: #11291e55;
    z-index: 99;
  }
  .workspace-main {
    margin-left: 0;
  }
  .mobile-menu {
    display: inline-flex;
  }
  .topbar {
    padding: 0 16px;
    height: 60px;
  }
  .breadcrumb {
    gap: 8px;
  }
  .breadcrumb > span,
  .breadcrumb > .el-icon,
  .topbar-divider,
  .topbar-actions > .status-label {
    display: none;
  }
  .workspace-content {
    padding: 22px 16px;
  }
  .workspace-footer {
    padding: 16px;
  }
}
</style>
