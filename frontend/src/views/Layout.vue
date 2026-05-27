<template>
  <div class="layout-container" ref="containerRef" @scroll="onScroll">
    <header
      class="layout-header"
      :class="{
        'header-scrolled': isScrolled,
        'header-compact': isCompact
      }"
    >
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
      </div>
    </header>
    <main class="layout-body">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
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

const containerRef = ref(null)
const isScrolled = ref(false)
const isCompact = ref(false)

const HEADER_HEIGHT = 60
const COMPACT_THRESHOLD = 200

const onScroll = () => {
  const container = containerRef.value
  if (!container) return

  const requirementBody = container.querySelector('.requirement-body')
  if (!requirementBody) return

  const headerBottom = HEADER_HEIGHT / 2
  const rect = requirementBody.getBoundingClientRect()

  isScrolled.value = rect.top <= headerBottom

  if (isScrolled.value) {
    const overflow = headerBottom - rect.top
    isCompact.value = overflow > COMPACT_THRESHOLD
  } else {
    isCompact.value = false
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  overflow-y: auto;
  background: #FFFFFF;
}

.layout-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: transparent;
  border-bottom: 1px solid transparent;
  transition:
    background-color 0.4s ease,
    border-color 0.4s ease,
    box-shadow 0.4s ease;
}

.layout-header.header-scrolled {
  background-color: rgba(255, 253, 249, 0.92);
  border-bottom-color: rgba(181, 201, 168, 0.2);
  box-shadow: 0 1px 8px rgba(156, 175, 136, 0.06);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.header-inner {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 32px;
  transition:
    height 0.4s ease,
    padding 0.4s ease,
    gap 0.4s ease;
}

.layout-header.header-compact .header-inner {
  height: 32px;
  padding: 0 16px;
  gap: 16px;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  transition: gap 0.4s ease;
}

.layout-header.header-compact .logo-area {
  gap: 6px;
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
  transition:
    width 0.4s ease,
    height 0.4s ease,
    font-size 0.4s ease,
    border-radius 0.4s ease;
}

.layout-header.header-compact .logo-icon {
  width: 22px;
  height: 22px;
  font-size: 11px;
  border-radius: 6px;
}

.logo-text {
  color: #1a1a1a;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.03em;
  transition: font-size 0.4s ease;
}

.layout-header.header-compact .logo-text {
  font-size: 12px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  justify-content: flex-end;
  transition: gap 0.4s ease;
}

.layout-header.header-compact .header-nav {
  gap: 2px;
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
  color: #1a1a1a;
  transition:
    all 0.25s ease,
    padding 0.4s ease,
    font-size 0.4s ease,
    gap 0.4s ease;
  user-select: none;
}

.nav-tab:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #000000;
}

.nav-tab.active {
  background: rgba(0, 0, 0, 0.08);
  color: #000000;
  font-weight: 600;
}

.layout-header.header-compact .nav-tab {
  padding: 4px 10px;
  font-size: 11px;
  gap: 3px;
  border-radius: 5px;
}

.layout-header.header-compact .nav-tab :deep(.el-icon) {
  font-size: 12px !important;
}

.layout-body {
  padding-top: 60px;
  min-height: 100vh;
}
</style>
