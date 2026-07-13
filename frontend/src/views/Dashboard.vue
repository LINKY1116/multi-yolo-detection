<template>
  <div class="dashboard-shell">
    <DynamicDecor />
    <el-header class="top-header">
      <div class="brand" @click="$router.push('/dashboard/home')">
        <div class="brand-mark">YOLO</div>
        <div class="brand-copy">
          <h2>智能视觉检测平台</h2>
          <p>Multi-scene AI Vision System</p>
        </div>
      </div>

      <el-menu
        :default-active="$route.path"
        mode="horizontal"
        router
        :ellipsis="false"
        class="top-menu"
      >
        <el-menu-item index="/dashboard/home">
          <el-icon><House /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/detection">
          <el-icon><Camera /></el-icon>
          <span>目标检测</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/history">
          <el-icon><Clock /></el-icon>
          <span>检测历史</span>
        </el-menu-item>
        <el-menu-item index="/dashboard/models">
          <el-icon><Setting /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
      </el-menu>

      <div class="header-actions">
        <el-tag class="soft-tag" effect="plain">{{ getPageTitle() }}</el-tag>
        <el-dropdown>
          <span class="user-chip">
            <el-icon><User /></el-icon>
            {{ $store.getters.currentUser?.username || '用户' }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="$router.push('/dashboard/home')">
                <el-icon><House /></el-icon>
                回到首页
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-main class="page-main">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>

    <FloatingAssistant />
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import FloatingAssistant from '../components/FloatingAssistant.vue'
import DynamicDecor from '../components/DynamicDecor.vue'
import {
  House,
  Camera,
  Clock,
  SwitchButton,
  User,
  ArrowDown,
  Setting
} from '@element-plus/icons-vue'

export default {
  name: 'Dashboard',
  components: {
    FloatingAssistant,
    DynamicDecor,
    House,
    Camera,
    Clock,
    SwitchButton,
    User,
    ArrowDown,
    Setting
  },
  mounted() {
    this.$store.dispatch('initializeAuth')
    if (!this.$store.getters.isAuthenticated) {
      this.$router.push('/login')
    }
  },
  methods: {
    getPageTitle() {
      const routeMap = {
        '/dashboard/home': '系统首页',
        '/dashboard/detection': '目标检测',
        '/dashboard/history': '检测历史',
        '/dashboard/models': '模型管理'
      }
      return routeMap[this.$route.path] || '智能视觉检测平台'
    },
    async handleLogout() {
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        this.$store.dispatch('logout')
        ElMessage.success('已退出登录')
        this.$router.push('/login')
      } catch {
        // 用户取消操作
      }
    }
  }
}
</script>

<style scoped>
.dashboard-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at 8% 8%, rgba(167, 139, 250, .16), transparent 28vw),
    radial-gradient(circle at 88% 12%, rgba(125, 211, 252, .16), transparent 30vw),
    linear-gradient(135deg, #fbfbff 0%, #f3f7ff 48%, #fff7f1 100%);
}

.top-header {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 82px !important;
  display: grid;
  grid-template-columns: minmax(245px, 330px) 1fr auto;
  align-items: center;
  gap: 18px;
  padding: 0 32px;
  border-bottom: 1px solid rgba(214, 226, 242, .78);
  background: rgba(255, 255, 255, .78);
  box-shadow: 0 14px 36px rgba(99, 102, 241, .08);
  backdrop-filter: blur(22px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 13px;
  cursor: pointer;
  user-select: none;
}

.brand-mark {
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: .5px;
  background: linear-gradient(135deg, #8b5cf6, #60a5fa 58%, #67e8f9);
  box-shadow: 0 16px 26px rgba(96, 165, 250, .24);
}

.brand-copy h2 {
  margin: 0;
  color: #27304f;
  font-size: 19px;
  font-weight: 900;
  line-height: 1.2;
}

.brand-copy p {
  margin: 5px 0 0;
  color: #8290ad;
  font-size: 12px;
  letter-spacing: .7px;
}

.top-menu {
  justify-content: center;
  border: 0 !important;
  background: transparent !important;
}

:deep(.el-menu--horizontal > .el-menu-item) {
  height: 48px;
  margin: 0 5px;
  padding: 0 18px;
  border-radius: 999px;
  border-bottom: 0 !important;
  color: #61708f !important;
  font-weight: 800;
  transition: all .22s ease;
}

:deep(.el-menu--horizontal > .el-menu-item:hover) {
  color: #5b6ee1 !important;
  background: rgba(238, 242, 255, .92) !important;
}

:deep(.el-menu--horizontal > .el-menu-item.is-active) {
  color: #4254c5 !important;
  background: linear-gradient(135deg, rgba(237, 233, 254, .95), rgba(219, 234, 254, .95)) !important;
  box-shadow: 0 12px 24px rgba(96, 165, 250, .13);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.soft-tag {
  height: 34px;
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(196, 181, 253, .55) !important;
  color: #6554c8 !important;
  background: rgba(245, 243, 255, .82) !important;
  font-weight: 800;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 10px 14px;
  border: 1px solid rgba(214, 226, 242, .92);
  border-radius: 999px;
  background: rgba(255, 255, 255, .88);
  color: #42506f;
  font-weight: 800;
  box-shadow: 0 10px 24px rgba(71, 85, 105, .06);
  transition: all .22s ease;
}

.user-chip:hover {
  border-color: rgba(147, 197, 253, .75);
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(96, 165, 250, .13);
}

.page-main {
  position: relative;
  z-index: 1;
  min-height: calc(100vh - 82px);
  padding: 30px;
  overflow-x: hidden;
}


.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity .24s ease, transform .24s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 1180px) {
  .top-header {
    grid-template-columns: 1fr;
    height: auto !important;
    padding: 16px 18px;
  }

  .top-menu {
    justify-content: flex-start;
    overflow-x: auto;
  }

  .header-actions {
    justify-content: space-between;
  }
}

@media (max-width: 700px) {
  .brand-copy p,
  .soft-tag {
    display: none;
  }

  .page-main {
    padding: 18px;
  }

  :deep(.el-menu--horizontal > .el-menu-item) {
    padding: 0 13px;
  }
}
</style>
