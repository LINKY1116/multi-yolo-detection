<template>
  <div class="login-page">
    <header class="login-brand">
      <span class="login-mark"
        ><el-icon><Aim /></el-icon></span
      ><strong>Multi YOLO</strong><span>视觉检测工作台</span>
    </header>
    <main class="login-main">
      <div class="login-form-area">
        <span class="eyebrow">WORKSPACE ACCESS</span>
        <h1>
          {{ mode === 'login' ? '登录工作空间' : mode === 'register' ? '创建账号' : '重置密码' }}
        </h1>
        <div class="login-tabs" v-if="mode !== 'reset'">
          <button :class="{ active: mode === 'login' }" @click="changeMode('login')">
            账号登录</button
          ><button :class="{ active: mode === 'register' }" @click="changeMode('register')">
            注册新账号
          </button>
        </div>
        <el-alert v-if="error" :title="error" type="error" show-icon @close="error = ''" /><el-form
          label-position="top"
          @submit.prevent="submit"
          ><el-form-item label="用户名"
            ><el-input
              v-model="username"
              size="large"
              placeholder="输入用户名"
              autocomplete="username"
              maxlength="80"
              :disabled="busy"
              ><template #prefix
                ><el-icon><User /></el-icon></template></el-input></el-form-item
          ><el-form-item :label="mode === 'reset' ? '新密码' : '密码'"
            ><el-input
              v-model="password"
              size="large"
              placeholder="输入密码"
              type="password"
              show-password
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              :disabled="busy"
              ><template #prefix
                ><el-icon><Lock /></el-icon></template></el-input></el-form-item
          ><el-form-item v-if="mode !== 'login'" label="确认密码"
            ><el-input
              v-model="confirm"
              size="large"
              placeholder="再次输入密码"
              type="password"
              show-password
              autocomplete="new-password"
              :disabled="busy"
          /></el-form-item>
          <div v-if="mode === 'login'" class="form-option">
            <el-checkbox v-model="remember">记住用户名</el-checkbox
            ><button type="button" @click="changeMode('reset')">忘记密码</button>
          </div>
          <el-button
            type="primary"
            size="large"
            native-type="submit"
            class="login-submit"
            :loading="busy"
            >{{ mode === 'login' ? '进入工作空间' : mode === 'register' ? '注册账号' : '确认重置'
            }}<el-icon v-if="!busy"><ArrowRight /></el-icon></el-button
          ><button
            v-if="mode === 'reset'"
            type="button"
            class="back-login"
            @click="changeMode('login')"
          >
            返回登录
          </button></el-form
        >
        <div class="login-status">
          <i class="status-dot" :class="{ off: !online }"></i
          >{{ online ? '检测服务已连接' : '检测服务未连接'
          }}<button
            type="button"
            @click="checkHealth"
            title="重新检查连接"
            aria-label="重新检查连接"
          >
            <el-icon><Refresh /></el-icon>
          </button>
        </div>
      </div>
    </main>
    <footer>Multi YOLO <span>Visual Intelligence Workspace</span></footer>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { api } from '../lib/workspace'
const router = useRouter(),
  store = useStore()
const mode = ref('login'),
  username = ref(localStorage.getItem('remembered_username') || ''),
  password = ref(''),
  confirm = ref(''),
  remember = ref(!!username.value),
  busy = ref(false),
  error = ref(''),
  online = ref(false)
function changeMode(value) {
  if (busy.value) return
  mode.value = value
  error.value = ''
  password.value = ''
  confirm.value = ''
}
async function checkHealth() {
  try {
    await api('/health', { timeout: 5000 })
    online.value = true
  } catch {
    online.value = false
  }
}
async function submit() {
  if (busy.value) return
  error.value = ''
  const name = username.value.trim()
  if (!name || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }
  if (mode.value !== 'login' && (password.value.length < 6 || password.value !== confirm.value)) {
    error.value = '密码至少 6 位，且两次输入须一致'
    return
  }
  busy.value = true
  try {
    const data = await api(mode.value === 'reset' ? '/reset_password' : `/${mode.value}`, {
      method: 'POST',
      data: { username: name, password: password.value },
    })
    if (mode.value === 'login') {
      store.commit('SET_USER', data.user)
      if (remember.value) localStorage.setItem('remembered_username', name)
      else localStorage.removeItem('remembered_username')
      router.push('/dashboard/detection')
    } else {
      ElMessage.success(mode.value === 'register' ? '注册成功，请登录' : '密码已重置')
      mode.value = 'login'
      password.value = ''
      confirm.value = ''
    }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
onMounted(checkHealth)
</script>
<style scoped>
.login-page {
  min-height: 100vh;
  background: #fcfdfc;
  display: flex;
  flex-direction: column;
  border-top: 4px solid #19684b;
}
.login-brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 30px 40px;
}
.login-brand strong {
  font-size: 22px;
  font-weight: 600;
}
.login-brand > span:last-child {
  font-size: 11px;
  padding-left: 18px;
  margin-left: 7px;
  border-left: 1px solid var(--line);
  color: #94a198;
}
.login-mark {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  background: var(--accent);
  color: white;
  border-radius: 7px;
  font-size: 23px;
}
.login-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 50px 24px 80px;
}
.login-form-area {
  width: 370px;
  max-width: 100%;
}
.login-form-area h1 {
  font-size: 28px;
  margin: 10px 0 26px;
}
.login-form-area > .eyebrow {
  font-size: 10px;
  color: #91a096;
}
.login-tabs {
  display: flex;
  gap: 25px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 27px;
}
.login-tabs button {
  background: transparent;
  border: 0;
  padding: 0 1px 12px;
  font-size: 13px;
  color: #8a978f;
}
.login-tabs button.active {
  color: var(--accent);
  border-bottom: 2px solid var(--accent);
}
.form-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: -7px 0 17px;
}
.form-option > button,
.back-login {
  border: 0;
  background: transparent;
  color: #708679;
  font-size: 12px;
}
.login-submit {
  width: 100%;
  height: 44px;
}
.login-submit .el-icon {
  margin-left: 13px;
}
.back-login {
  display: block;
  margin: 18px auto 0;
}
.login-status {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 30px;
  font-size: 10px;
  color: #99a59d;
}
.login-status button {
  display: inline-flex;
  border: 0;
  background: transparent;
  color: #99a59d;
}
footer {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 20px 40px;
  border-top: 1px solid var(--line);
  font-size: 10px;
  color: #a5afa8;
}
@media (max-width: 600px) {
  .login-brand {
    padding: 24px;
  }
  .login-brand > span:last-child {
    display: none;
  }
  footer {
    padding: 20px 24px;
  }
}
</style>
