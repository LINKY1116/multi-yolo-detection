<template>
  <div class="home-page">
    <section class="hero-card">
      <div class="hero-text">
        <el-tag class="hero-badge" effect="plain">YOLO 多场景目标检测</el-tag>
        <h1>让检测、分析与管理<br>像使用正式网站一样顺手</h1>
        <p>
          支持图片、视频与摄像头实时检测，可切换病虫害、花卉、火灾、无人机等 YOLO 模型，
          并结合历史记录与 AI 分析生成更直观的识别结果。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="$router.push('/dashboard/detection')">
            开始检测
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
          <el-button size="large" plain @click="$router.push('/dashboard/models')">
            管理模型
          </el-button>
        </div>
      </div>
      <div class="hero-visual">
        <div class="vision-window">
          <div class="window-top">
            <span></span><span></span><span></span>
          </div>
          <div class="scan-box">
            <div class="corner c1"></div>
            <div class="corner c2"></div>
            <div class="corner c3"></div>
            <div class="corner c4"></div>
            <el-icon><Aim /></el-icon>
            <p>AI Vision Detecting</p>
          </div>
          <div class="result-pills">
            <span>目标数量 12</span>
            <span>平均置信度 92%</span>
            <span>建议复核 0</span>
          </div>
        </div>
      </div>
    </section>

    <el-row :gutter="22" class="feature-grid">
      <el-col :xs="24" :sm="12" :lg="6" v-for="item in features" :key="item.title">
        <el-card class="feature-card" shadow="hover" @click="$router.push(item.path)">
          <div class="feature-icon" :class="item.className">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="22" class="content-row">
      <el-col :xs="24" :lg="15">
        <el-card class="workflow-card" shadow="hover">
          <template #header>
            <div class="section-title">
              <span>系统使用流程</span>
              <small>从模型选择到结果分析，流程更清楚</small>
            </div>
          </template>
          <div class="workflow">
            <div class="step" v-for="(step, index) in steps" :key="step.title">
              <div class="step-index">0{{ index + 1 }}</div>
              <div>
                <h4>{{ step.title }}</h4>
                <p>{{ step.desc }}</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="notice-card" shadow="hover">
          <template #header>
            <div class="section-title">
              <span>项目亮点</span>
              <small>适合课程展示与后续扩展</small>
            </div>
          </template>
          <div class="notice-list">
            <div class="notice-item" v-for="item in highlights" :key="item">
              <el-icon><Check /></el-icon>
              <span>{{ item }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import {
  ArrowRight,
  Aim,
  Picture,
  VideoCamera,
  Clock,
  Setting,
  ChatDotRound,
  Check
} from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    ArrowRight,
    Aim,
    Picture,
    VideoCamera,
    Clock,
    Setting,
    ChatDotRound,
    Check
  },
  data() {
    return {
      features: [
        { title: '图片检测', desc: '上传图片后自动识别目标，展示检测框、类别与置信度。', icon: 'Picture', path: '/dashboard/detection', className: 'lavender' },
        { title: '视频检测', desc: '处理视频文件并生成带检测框的结果视频和统计信息。', icon: 'VideoCamera', path: '/dashboard/detection', className: 'blue' },
        { title: '历史记录', desc: '保存检测结果，支持查看详情、下载结果和批量管理。', icon: 'Clock', path: '/dashboard/history', className: 'mint' },
        { title: '模型中心', desc: '上传、加载、删除不同场景的 YOLO 模型，便于扩展。', icon: 'Setting', path: '/dashboard/models', className: 'peach' }
      ],
      steps: [
        { title: '选择模型', desc: '在模型管理中加载合适的 YOLO 模型，匹配当前检测场景。' },
        { title: '上传或采集', desc: '选择图片、视频或摄像头模式，提交需要识别的数据。' },
        { title: '查看结果', desc: '系统返回检测框、类别、置信度、数量统计和结果文件。' },
        { title: 'AI 分析', desc: '根据检测内容生成自然语言报告，也可围绕结果继续提问。' }
      ],
      highlights: [
        '前后端分离，页面结构更清晰',
        '多模型切换，支持不同检测场景',
        '检测历史可追溯，方便复查结果',
        'AI 分析增强展示效果',
        '柔和浅色风格，更像正式网站'
      ]
    }
  }
}
</script>

<style scoped>
.home-page {
  max-width: 1380px;
  margin: 0 auto;
}

.hero-card {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.04fr) minmax(360px, .96fr);
  gap: 30px;
  align-items: center;
  min-height: 410px;
  padding: 44px;
  border: 1px solid rgba(214, 226, 242, .86);
  border-radius: 34px;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(255,255,255,.94), rgba(245, 243, 255, .82)),
    radial-gradient(circle at 88% 22%, rgba(191, 219, 254, .72), transparent 34%);
  box-shadow: 0 28px 70px rgba(99, 102, 241, .11);
}

.hero-card::after {
  content: '';
  position: absolute;
  right: -70px;
  bottom: -95px;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: rgba(254, 215, 170, .45);
  filter: blur(2px);
}

.hero-text,
.hero-visual {
  position: relative;
  z-index: 1;
}

.hero-badge {
  height: 34px;
  padding: 0 14px;
  border-color: rgba(196, 181, 253, .7) !important;
  color: #6959d7 !important;
  background: rgba(245, 243, 255, .8) !important;
  font-weight: 800;
}

.hero-text h1 {
  margin: 18px 0 16px;
  color: #24304f;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.1;
  letter-spacing: -1.8px;
  font-weight: 950;
}

.hero-text p {
  max-width: 660px;
  color: #66728f;
  font-size: 16px;
  line-height: 1.9;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 28px;
}

.vision-window {
  width: min(100%, 500px);
  margin-left: auto;
  padding: 18px;
  border: 1px solid rgba(207, 216, 235, .9);
  border-radius: 28px;
  background: rgba(255, 255, 255, .72);
  box-shadow: 0 28px 60px rgba(71, 85, 105, .13);
  backdrop-filter: blur(16px);
}

.window-top {
  display: flex;
  gap: 8px;
  padding: 0 0 16px;
}

.window-top span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #dbe4f2;
}

.window-top span:nth-child(1) { background: #fda4af; }
.window-top span:nth-child(2) { background: #fde68a; }
.window-top span:nth-child(3) { background: #86efac; }

.scan-box {
  position: relative;
  height: 245px;
  display: grid;
  place-items: center;
  text-align: center;
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(238, 242, 255, .9), rgba(224, 242, 254, .78)),
    repeating-linear-gradient(0deg, transparent 0 20px, rgba(148, 163, 184, .12) 20px 21px);
  overflow: hidden;
}

.scan-box::after {
  content: '';
  position: absolute;
  left: 12%;
  right: 12%;
  top: 46%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, .72), transparent);
  box-shadow: 0 0 22px rgba(99, 102, 241, .5);
}

.scan-box .el-icon {
  color: #6d79df;
  font-size: 58px;
}

.scan-box p {
  margin-top: 12px;
  color: #6b728f;
  font-weight: 900;
  letter-spacing: .8px;
}

.corner {
  position: absolute;
  width: 38px;
  height: 38px;
  border-color: #8b5cf6;
}
.c1 { top: 32px; left: 38px; border-top: 3px solid; border-left: 3px solid; }
.c2 { top: 32px; right: 38px; border-top: 3px solid; border-right: 3px solid; }
.c3 { bottom: 32px; left: 38px; border-bottom: 3px solid; border-left: 3px solid; }
.c4 { bottom: 32px; right: 38px; border-bottom: 3px solid; border-right: 3px solid; }

.result-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.result-pills span {
  padding: 8px 12px;
  border-radius: 999px;
  color: #52607d;
  background: rgba(248, 250, 252, .92);
  border: 1px solid rgba(226, 232, 240, .9);
  font-size: 12px;
  font-weight: 800;
}

.feature-grid,
.content-row {
  margin-top: 24px;
}

.feature-card {
  height: 100%;
  cursor: pointer;
  transition: transform .22s ease, box-shadow .22s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  margin-bottom: 18px;
  font-size: 25px;
}

.feature-icon.lavender { color: #7c3aed; background: #f3e8ff; }
.feature-icon.blue { color: #7c83f5; background: #dbeafe; }
.feature-icon.mint { color: #059669; background: #d1fae5; }
.feature-icon.peach { color: #ea580c; background: #ffedd5; }

.feature-card h3 {
  margin: 0 0 10px;
  color: #27304f;
  font-size: 19px;
  font-weight: 900;
}

.feature-card p {
  margin: 0;
  color: #71809d;
  line-height: 1.75;
}

.section-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.section-title span {
  color: #27304f;
  font-size: 18px;
  font-weight: 900;
}

.section-title small {
  color: #8a96ad;
}

.workflow {
  display: grid;
  gap: 16px;
}

.step {
  display: flex;
  gap: 16px;
  padding: 18px;
  border: 1px solid rgba(226, 232, 240, .85);
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255,255,255,.88), rgba(248,250,252,.72));
}

.step-index {
  width: 50px;
  height: 50px;
  flex: none;
  display: grid;
  place-items: center;
  border-radius: 16px;
  color: #5b6ee1;
  background: #eef2ff;
  font-weight: 950;
}

.step h4 {
  margin: 0 0 7px;
  color: #27304f;
  font-weight: 900;
}

.step p {
  margin: 0;
  color: #71809d;
  line-height: 1.7;
}

.notice-list {
  display: grid;
  gap: 15px;
}

.notice-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 15px;
  border-radius: 18px;
  color: #52607d;
  background: rgba(248, 250, 252, .78);
  font-weight: 800;
}

.notice-item .el-icon {
  color: #10b981;
  font-size: 18px;
}

@media (max-width: 1080px) {
  .hero-card {
    grid-template-columns: 1fr;
    padding: 30px;
  }

  .vision-window {
    margin: 0;
  }
}

@media (max-width: 640px) {
  .hero-card {
    padding: 24px;
    border-radius: 26px;
  }

  .hero-actions .el-button {
    width: 100%;
  }

  .section-title {
    display: block;
  }

  .section-title small {
    display: block;
    margin-top: 6px;
  }
}
</style>
