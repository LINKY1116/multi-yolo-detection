<template>
  <div class="login-container">
    <div class="login-orbit" aria-hidden="true">
      <span></span><span></span><span></span>
    </div>

    <div class="login-card">
      <div class="system-title">
        <div class="brand-row">
          <div class="brand-logo">YOLO</div>
          <div>
            <strong>智能视觉检测平台</strong>
            <p>AI Vision Detection System</p>
          </div>
        </div>
        <h1>多场景目标检测，让识别结果更直观</h1>
        <p class="hero-desc">
          支持图片、视频、摄像头实时检测，结合模型管理、历史记录与 AI 分析，适合课程展示与后续扩展。
        </p>
        <div class="hero-pills">
          <span>图片检测</span>
          <span>视频检测</span>
          <span>AI 分析</span>
          <span>模型管理</span>
        </div>
      </div>
      
      <div class="login-form-container">
        <div class="form-header">
          <el-tag class="welcome-tag" effect="plain">Welcome Back</el-tag>
          <h2>登录系统</h2>
          <p>输入账号密码后继续使用检测平台</p>
        </div>
        
        <el-form 
          ref="loginForm" 
          :model="loginData" 
          :rules="rules" 
          class="login-form"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginData.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              size="large"
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginData.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              size="large"
              show-password
              clearable
            />
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              class="login-button"
              :loading="$store.state.isLoading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="form-footer">
          <el-link @click="showRegister = true">注册账号</el-link>
          <el-link @click="openForgotDialog">忘记密码</el-link>
        </div>
        
        <div class="footer-info">
          <span>Tip：默认演示账号可使用后端初始化的 admin / admin123</span>
        </div>
      </div>
    </div>
    
    <!-- 注册对话框 -->
    <el-dialog v-model="showRegister" title="用户注册" width="430px" class="auth-dialog">
      <el-form 
        ref="registerForm" 
        :model="registerData" 
        :rules="registerRules"
        label-position="top"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerData.username" placeholder="请输入用户名" prefix-icon="User" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="registerData.password" 
            type="password" 
            placeholder="请输入密码" 
            prefix-icon="Lock"
            show-password 
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="registerData.confirmPassword" 
            type="password" 
            placeholder="请确认密码" 
            prefix-icon="Lock"
            show-password 
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="$store.state.isLoading"
          @click="handleRegister"
        >
          注册
        </el-button>
      </template>
    </el-dialog>

    <!-- 忘记密码对话框 -->
    <el-dialog v-model="showForgot" title="找回密码" width="470px" class="auth-dialog" @closed="resetForgotForm">
      <div class="forgot-intro">
        <div class="intro-icon">?</div>
        <div>
          <strong>重置登录密码</strong>
          <p>为便于课程演示，系统采用“用户名 + 演示校验码 + 新密码”的方式完成密码重置。</p>
        </div>
      </div>

      <el-form
        ref="forgotForm"
        :model="forgotData"
        :rules="forgotRules"
        label-position="top"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="forgotData.username" placeholder="请输入要重置的用户名" prefix-icon="User" clearable />
        </el-form-item>

        <el-form-item label="身份校验码" prop="code">
          <div class="code-row">
            <el-input v-model="forgotData.code" placeholder="请输入校验码" prefix-icon="Key" clearable />
            <el-button :disabled="codeCountdown > 0" @click="sendResetCode">
              {{ codeCountdown > 0 ? `${codeCountdown}s` : '获取校验码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="forgotData.newPassword"
            type="password"
            placeholder="请输入新密码，至少 6 位"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="forgotData.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showForgot = false">取消</el-button>
        <el-button type="primary" :loading="$store.state.isLoading" @click="handleResetPassword">
          确认重置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'

export default {
  name: 'Login',
  data() {
    const validatePassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'))
      } else if (value.length < 6) {
        callback(new Error('密码长度不能少于6位'))
      } else {
        callback()
      }
    }
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请确认密码'))
      } else if (value !== this.registerData.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }

    const validateResetConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请确认新密码'))
      } else if (value !== this.forgotData.newPassword) {
        callback(new Error('两次输入的新密码不一致'))
      } else {
        callback()
      }
    }

    const validateResetCode = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请输入校验码'))
      } else if (!this.generatedCode) {
        callback(new Error('请先获取校验码'))
      } else if (String(value).trim() !== String(this.generatedCode)) {
        callback(new Error('校验码不正确'))
      } else {
        callback()
      }
    }
    
    return {
      loginData: {
        username: '',
        password: ''
      },
      registerData: {
        username: '',
        password: '',
        confirmPassword: ''
      },
      forgotData: {
        username: '',
        code: '',
        newPassword: '',
        confirmPassword: ''
      },
      showRegister: false,
      showForgot: false,
      generatedCode: '',
      codeCountdown: 0,
      codeTimer: null,
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, validator: validatePassword, trigger: 'blur' }
        ]
      },
      registerRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '用户名长度在3到20个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, validator: validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, validator: validateConfirmPassword, trigger: 'blur' }
        ]
      },
      forgotRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        code: [
          { required: true, validator: validateResetCode, trigger: 'blur' }
        ],
        newPassword: [
          { required: true, validator: validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, validator: validateResetConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },
  mounted() {
    if (this.$store.getters.isAuthenticated) {
      this.$router.push('/dashboard')
    }
    this.$store.dispatch('initializeAuth')
  },
  beforeUnmount() {
    if (this.codeTimer) clearInterval(this.codeTimer)
  },
  methods: {
    async handleLogin() {
      try {
        await this.$refs.loginForm.validate()
        const result = await this.$store.dispatch('login', this.loginData)
        
        if (result.success) {
          ElMessage.success(result.message)
          this.$router.push('/dashboard')
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        console.error('登录失败:', error)
      }
    },
    
    async handleRegister() {
      try {
        await this.$refs.registerForm.validate()
        const result = await this.$store.dispatch('register', {
          username: this.registerData.username,
          password: this.registerData.password
        })
        
        if (result.success) {
          ElMessage.success(result.message)
          this.showRegister = false
          this.registerData = { username: '', password: '', confirmPassword: '' }
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        console.error('注册失败:', error)
      }
    },

    openForgotDialog() {
      this.showForgot = true
      this.forgotData.username = this.loginData.username || ''
    },

    sendResetCode() {
      if (!this.forgotData.username) {
        ElMessage.warning('请先输入用户名')
        return
      }
      this.generatedCode = String(Math.floor(100000 + Math.random() * 900000))
      this.codeCountdown = 60
      if (this.codeTimer) clearInterval(this.codeTimer)
      this.codeTimer = setInterval(() => {
        this.codeCountdown -= 1
        if (this.codeCountdown <= 0) {
          clearInterval(this.codeTimer)
          this.codeTimer = null
        }
      }, 1000)
      ElMessage.info(`演示校验码：${this.generatedCode}`)
    },

    async handleResetPassword() {
      try {
        await this.$refs.forgotForm.validate()
        const result = await this.$store.dispatch('resetPassword', {
          username: this.forgotData.username,
          password: this.forgotData.newPassword
        })
        if (result.success) {
          ElMessage.success(result.message || '密码重置成功，请使用新密码登录')
          this.loginData.username = this.forgotData.username
          this.loginData.password = ''
          this.showForgot = false
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        console.error('重置密码失败:', error)
      }
    },

    resetForgotForm() {
      this.forgotData = { username: '', code: '', newPassword: '', confirmPassword: '' }
      this.generatedCode = ''
      this.codeCountdown = 0
      if (this.codeTimer) {
        clearInterval(this.codeTimer)
        this.codeTimer = null
      }
      this.$refs.forgotForm?.clearValidate?.()
    }
  }
}
</script>

<style scoped>
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 34px;
  background:
    radial-gradient(circle at 16% 12%, rgba(191, 219, 254, .55), transparent 30%),
    radial-gradient(circle at 86% 80%, rgba(253, 224, 203, .54), transparent 32%),
    linear-gradient(135deg, #fbfcff 0%, #f4f0ff 45%, #fff8f0 100%);
  overflow: hidden;
}

.login-orbit span {
  position: absolute;
  display: block;
  border-radius: 999px;
  border: 1px solid rgba(165, 180, 252, .28);
  background: rgba(255, 255, 255, .22);
  animation: orbitFloat 9s ease-in-out infinite;
}

.login-orbit span:nth-child(1) { width: 280px; height: 280px; left: -80px; top: -80px; }
.login-orbit span:nth-child(2) { width: 170px; height: 170px; right: 8%; top: 12%; animation-delay: -2s; }
.login-orbit span:nth-child(3) { width: 240px; height: 240px; right: -80px; bottom: -90px; animation-delay: -4s; }

.login-card {
  position: relative;
  z-index: 1;
  width: min(100%, 1040px);
  min-height: 628px;
  display: grid;
  grid-template-columns: 1.08fr .92fr;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, .75);
  border-radius: 36px;
  background: rgba(255, 255, 255, .72);
  box-shadow: 0 34px 90px rgba(129, 140, 248, .20);
  backdrop-filter: blur(24px);
}

.system-title {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 58px;
  color: #27304f;
  background:
    radial-gradient(circle at 18% 18%, rgba(255,255,255,.70), transparent 22%),
    linear-gradient(145deg, rgba(224, 242, 254, .86), rgba(237, 233, 254, .88) 56%, rgba(255, 237, 213, .72));
}

.system-title::after {
  content: '';
  position: absolute;
  right: -58px;
  bottom: -58px;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: rgba(255, 255, 255, .28);
}

.brand-row {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 34px;
}

.brand-logo {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  border-radius: 20px;
  color: #fff;
  font-weight: 950;
  background: linear-gradient(135deg, #8fb8ff, #bca9ff 55%, #ffc9ad);
  box-shadow: 0 18px 34px rgba(129, 140, 248, .28);
}

.brand-row strong {
  font-size: 18px;
  font-weight: 950;
}

.brand-row p {
  margin: 4px 0 0;
  color: #7c88a5;
  font-size: 12px;
  letter-spacing: .8px;
}

.system-title h1 {
  position: relative;
  z-index: 1;
  max-width: 440px;
  margin: 0;
  font-size: 42px;
  line-height: 1.15;
  font-weight: 950;
  letter-spacing: -1.5px;
}

.hero-desc {
  position: relative;
  z-index: 1;
  max-width: 440px;
  margin: 20px 0 0;
  color: #61708f;
  font-size: 16px;
  line-height: 1.9;
}

.hero-pills {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}

.hero-pills span {
  padding: 8px 13px;
  border: 1px solid rgba(255,255,255,.62);
  border-radius: 999px;
  background: rgba(255,255,255,.45);
  color: #556381;
  font-size: 13px;
  font-weight: 850;
}

.login-form-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 58px 52px;
  background: rgba(255, 255, 255, .88);
}

.form-header {
  margin-bottom: 28px;
}

.welcome-tag {
  height: 32px;
  margin-bottom: 16px;
  border-color: rgba(196, 181, 253, .72) !important;
  color: #6554c8 !important;
  background: rgba(245, 243, 255, .86) !important;
  font-weight: 850;
}

.form-header h2 {
  margin: 0 0 10px;
  color: #27304f;
  font-size: 28px;
  font-weight: 950;
  letter-spacing: -.5px;
}

.form-header p {
  margin: 0;
  color: #7c88a5;
  font-size: 14px;
}

.login-form {
  margin-bottom: 18px;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-input__wrapper) {
  min-height: 52px;
  padding: 0 16px;
  border-radius: 17px;
}

:deep(.el-input__inner) {
  height: 52px;
  line-height: 52px;
  font-weight: 650;
}

.login-button {
  width: 100%;
  height: 52px;
  margin-top: 4px;
  border: none;
  border-radius: 17px;
  background: linear-gradient(135deg, #8ea7ff, #9ed8ff 55%, #ffc3a7);
  font-size: 16px;
  font-weight: 950;
  letter-spacing: 1px;
  box-shadow: 0 16px 34px rgba(129, 140, 248, .24);
}

.login-button:hover {
  box-shadow: 0 20px 42px rgba(129, 140, 248, .34);
}

.form-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  margin-bottom: 22px;
}

:deep(.el-link) {
  font-weight: 850;
}

.footer-info {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, .76);
  color: #8b98b5;
  font-size: 12px;
  line-height: 1.6;
}

.forgot-intro {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(239, 246, 255, .92), rgba(245, 243, 255, .92));
}

.intro-icon {
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #fff;
  font-size: 20px;
  font-weight: 950;
  background: linear-gradient(135deg, #93c5fd, #c4b5fd);
}

.forgot-intro strong {
  color: #27304f;
  font-weight: 950;
}

.forgot-intro p {
  margin: 6px 0 0;
  color: #70809f;
  font-size: 13px;
  line-height: 1.65;
}

.code-row {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 112px;
  gap: 10px;
}

:deep(.auth-dialog .el-dialog) {
  border-radius: 26px;
}

@keyframes orbitFloat {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(18px, -22px, 0) scale(1.05); }
}

@media (max-width: 900px) {
  .login-card {
    grid-template-columns: 1fr;
    max-width: 500px;
  }
  .system-title {
    padding: 38px 34px;
  }
  .system-title h1 {
    font-size: 30px;
  }
  .login-form-container {
    padding: 38px 32px;
  }
}

@media (max-width: 520px) {
  .login-container {
    padding: 18px;
  }
  .code-row {
    grid-template-columns: 1fr;
  }
}
</style>
