<template>
  <div class="layout-container">
    <header class="layout-header">
      <div class="header-inner">
        <div class="logo-area">
          <div class="logo-icon">P</div>
          <span class="logo-text">项目配置管理</span>
        </div>
        <nav class="header-nav">
          <div
            v-for="tab in tabs"
            :key="tab.path"
            :class="['nav-tab', { active: activeTab === tab.path }]"
            @click="handleTabClick(tab.path)"
          >
            <el-icon :size="16"><component :is="tab.icon" /></el-icon>
            <span>{{ tab.label }}</span>
          </div>
        </nav>
        <div class="header-right">
          <span class="version-text">v1.0.0</span>
        </div>
      </div>
    </header>
    <main class="layout-body">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { List, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const activeTab = computed(() => route.path)

const tabs = [
  { path: '/requirement', label: '需求汇总表', icon: List },
  { path: '/project', label: '项目配置表', icon: Setting },
]

const handleTabClick = (path) => {
  router.push(path)
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
}

.layout-header {
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  border-bottom: 1px solid rgba(200, 215, 235, 0.4);
  overflow: hidden;
}

.layout-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 120% 80% at 20% 60%, rgba(190, 215, 245, 0.5) 0%, transparent 60%),
    radial-gradient(ellipse 100% 90% at 80% 40%, rgba(210, 225, 250, 0.4) 0%, transparent 55%),
    radial-gradient(ellipse 80% 60% at 50% 80%, rgba(230, 240, 255, 0.6) 0%, transparent 50%),
    radial-gradient(ellipse 60% 40% at 70% 70%, rgba(200, 220, 248, 0.3) 0%, transparent 45%),
    radial-gradient(ellipse 140% 100% at 30% 30%, rgba(220, 235, 255, 0.35) 0%, transparent 50%),
    linear-gradient(180deg, #e8f0fa 0%, #f0f5fd 30%, #f5f9ff 60%, #eaf2fb 100%);
  z-index: 0;
}

.layout-header::after {
  content: '';
  position: absolute;
  top: -20%;
  left: 40%;
  width: 35%;
  height: 80%;
  background: radial-gradient(ellipse, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0.2) 40%, transparent 70%);
  filter: blur(10px);
  z-index: 1;
  pointer-events: none;
}

.header-inner {
  position: relative;
  z-index: 2;
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 32px;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.logo-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #7eb8e0 0%, #a8d0ec 50%, #c4dff4 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(120, 175, 220, 0.3);
}

.logo-text {
  color: #3a5a80;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #4a6a8a;
  transition: all 0.25s ease;
  user-select: none;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.nav-tab:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #2a4a6a;
}

.nav-tab.active {
  background: rgba(255, 255, 255, 0.6);
  color: #2a6ab0;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(100, 160, 220, 0.12);
}

.header-right {
  flex-shrink: 0;
}

.version-text {
  color: #8aa0b8;
  font-size: 12px;
}

.layout-body {
  flex: 1;
  overflow: auto;
  padding: 24px;
}
</style>
