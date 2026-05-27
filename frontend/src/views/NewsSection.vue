<template>
  <section class="news-section">
    <div class="news-inner">
      <div class="news-header">
        <div class="news-header-line"></div>
        <h2 class="news-title">下 载 中 心</h2>
        <p class="news-subtitle">DOWNLOAD CENTER</p>
        <div class="news-header-line"></div>
      </div>

      <div class="news-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="news-tab"
          :class="{ active: currentTab === tab.key }"
          @click="currentTab = tab.key"
        >
          {{ tab.label }}
          <span class="news-tab-indicator" v-if="currentTab === tab.key"></span>
        </button>
      </div>

      <div class="news-grid">
        <a
          v-for="item in filteredNews"
          :key="item.id"
          class="news-item"
          href="javascript:void(0)"
        >
          <div class="news-item-date">
            <span class="news-item-day">{{ item.day }}</span>
            <span class="news-item-month">{{ item.month }}</span>
          </div>
          <div class="news-item-body">
            <h4 class="news-item-title">{{ item.title }}</h4>
            <p class="news-item-desc">{{ item.desc }}</p>
          </div>
          <div class="news-item-arrow">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
        </a>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'

const currentTab = ref('all')

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'update', label: '版本更新' },
  { key: 'notice', label: '公告通知' },
  { key: 'insight', label: '行业洞察' }
]

const newsList = [
  {
    id: 1,
    category: 'update',
    day: '17',
    month: '2026-05',
    title: 'v3.2.0 版本发布：新增任务模块化管理与智能排序功能',
    desc: '本次更新引入模块化任务架构，支持自定义模块创建与管理，同时优化了任务排序算法，提升日常使用效率。'
  },
  {
    id: 2,
    category: 'notice',
    day: '15',
    month: '2026-05',
    title: '系统维护通知：5月20日凌晨2:00-4:00例行维护',
    desc: '为保障系统稳定运行，将于5月20日凌晨进行例行维护升级，届时服务将短暂不可用，请提前做好安排。'
  },
  {
    id: 3,
    category: 'insight',
    day: '12',
    month: '2026-05',
    title: '2026年项目管理趋势：AI驱动的智能工作流正在重塑团队协作',
    desc: '随着人工智能技术的深入应用，项目管理工具正从被动记录转向主动建议，智能工作流成为团队效率提升的关键。'
  },
  {
    id: 4,
    category: 'update',
    day: '08',
    month: '2026-05',
    title: 'v3.1.5 热修复：解决待办任务延期标记显示异常问题',
    desc: '修复了部分场景下待办任务延期标记未正确显示的问题，同时优化了剪贴板复制功能的兼容性。'
  },
  {
    id: 5,
    category: 'notice',
    day: '05',
    month: '2026-05',
    title: '功能建议征集：参与产品路线图规划，提交您的需求',
    desc: '我们正在收集用户反馈以规划下一季度产品路线图，欢迎提交功能建议与改进意见。'
  },
  {
    id: 6,
    category: 'insight',
    day: '01',
    month: '2026-05',
    title: '高效团队的秘密：如何用结构化思维管理复杂项目需求',
    desc: '结构化思维不仅适用于个人决策，更是团队管理复杂项目的核心方法论，本文探讨其在需求管理中的实践应用。'
  }
]

const filteredNews = computed(() => {
  if (currentTab.value === 'all') return newsList
  return newsList.filter(n => n.category === currentTab.value)
})
</script>

<style scoped>
.news-section {
  background: #E8EBED;
  padding: 80px 24px 120px;
}

.news-inner {
  max-width: 1100px;
  margin: 0 auto;
}

.news-header {
  text-align: center;
  margin-bottom: 48px;
}

.news-header-line {
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #c9a96e, transparent);
  margin: 0 auto 20px;
}

.news-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 2.25rem;
  font-weight: 600;
  color: #2D3748;
  letter-spacing: 0.2em;
  margin: 0 0 8px;
}

.news-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  font-weight: 300;
  color: #718096;
  letter-spacing: 0.3em;
  margin: 0 0 20px;
  text-transform: uppercase;
}

.news-tabs {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 48px;
}

.news-tab {
  position: relative;
  background: none;
  border: none;
  color: rgba(45, 55, 72, 0.4);
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  letter-spacing: 0.1em;
  cursor: pointer;
  padding: 8px 4px;
  transition: color 0.3s ease;
}

.news-tab:hover {
  color: rgba(45, 55, 72, 0.7);
}

.news-tab.active {
  color: #2D3748;
}

.news-tab-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: #2D3748;
}

.news-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}

.news-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid rgba(45, 55, 72, 0.08);
  text-decoration: none;
  transition: background 0.3s ease;
  cursor: pointer;
}

.news-item:hover {
  background: rgba(45, 55, 72, 0.03);
}

.news-item:hover .news-item-arrow {
  opacity: 1;
  transform: translateX(4px);
  color: #2D3748;
}

.news-item-date {
  flex-shrink: 0;
  width: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 2px;
}

.news-item-day {
  font-family: 'Noto Serif SC', serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(45, 55, 72, 0.4);
  line-height: 1;
  letter-spacing: 0.05em;
}

.news-item-month {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 11px;
  color: rgba(45, 55, 72, 0.3);
  margin-top: 4px;
  letter-spacing: 0.05em;
}

.news-item-body {
  flex: 1;
  min-width: 0;
}

.news-item-title {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: rgba(45, 55, 72, 0.85);
  line-height: 1.6;
  margin: 0 0 6px;
  letter-spacing: 0.03em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-item-desc {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 12px;
  color: rgba(45, 55, 72, 0.45);
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-item-arrow {
  flex-shrink: 0;
  color: rgba(45, 55, 72, 0.25);
  opacity: 0;
  transform: translateX(0);
  transition: all 0.3s ease;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .news-section {
    padding: 60px 16px 80px;
  }

  .news-grid {
    grid-template-columns: 1fr;
  }

  .news-title {
    font-size: 1.75rem;
  }

  .news-tabs {
    gap: 20px;
  }
}
</style>
