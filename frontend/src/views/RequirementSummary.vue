<template>
  <div class="requirement-summary">
    <HeroBanner />

    <div class="requirement-body">
      <div class="page-header">
        <div class="page-header-center">
          <h1 class="page-title">Android</h1>
        </div>
        <div class="page-header-right">
          <el-button size="small" :icon="Edit" @click="handleEditModule" :disabled="!currentModuleId">重命名</el-button>
          <el-button size="small" type="primary" :icon="CopyDocument" @click="handleCopyToClipboard" :disabled="!currentModuleId">复制到剪贴板</el-button>
        </div>
      </div>

      <div class="module-bar">
        <div class="module-tabs">
          <div
            v-for="mod in modules"
            :key="mod.id"
            class="module-tab"
            :class="{ active: currentModuleId === mod.id }"
            @click="selectModule(mod.id)"
          >
            <span class="module-tab-name">{{ mod.name }}</span>
            <el-icon class="module-tab-close" @click.stop="handleDeleteModule(mod)"><Close /></el-icon>
          </div>
          <el-button size="small" :icon="Plus" @click="showAddModule = true" text>新增模块</el-button>
        </div>
      </div>

      <div v-if="currentModuleId" class="task-content">
        <div class="task-section">
          <div class="section-header">
            <div class="section-title-group">
              <div class="section-dot today-dot"></div>
              <h3 class="section-title">今日任务</h3>
              <span class="section-count">{{ todayCount }}</span>
            </div>
          </div>
          <TodayTaskList :module-id="currentModuleId" ref="todayTaskRef" @moved-to-todo="onMovedToTodo" />
        </div>
        <div class="task-section">
          <div class="section-header">
            <div class="section-title-group">
              <div class="section-dot todo-dot"></div>
              <h3 class="section-title">待办任务</h3>
              <span class="section-count">{{ todoCount }}</span>
            </div>
          </div>
          <TodoPool :module-id="currentModuleId" ref="todoPoolRef" @moved-to-today="onMovedToToday" />
        </div>
      </div>
      <div v-else class="empty-area">
        <div class="empty-bg"></div>
        <el-empty description="请先创建一个任务模块" />
      </div>
    </div>

    <AboutSection />
    <DateRoulette />
    <ConcertSection />

    <el-dialog v-model="showAddModule" title="新增任务模块" width="400px" @close="newModuleName = ''">
      <el-form @submit.prevent="handleAddModule">
        <el-form-item label="模块名称">
          <el-input v-model="newModuleName" placeholder="请输入模块名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddModule = false">取消</el-button>
        <el-button type="primary" @click="handleAddModule">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRenameModule" title="重命名任务模块" width="400px">
      <el-form @submit.prevent="handleRenameModule">
        <el-form-item label="模块名称">
          <el-input v-model="renameValue" placeholder="请输入新名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRenameModule = false">取消</el-button>
        <el-button type="primary" @click="handleRenameModule">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, CopyDocument, Close } from '@element-plus/icons-vue'
import TodayTaskList from './TodayTaskList.vue'
import TodoPool from './TodoPool.vue'
import HeroBanner from './HeroBanner.vue'
import AboutSection from './AboutSection.vue'
import DateRoulette from './DateRoulette.vue'
import ConcertSection from './ConcertSection.vue'
import {
  getTaskModules,
  createTaskModule,
  updateTaskModule,
  deleteTaskModule,
  checkPostpone
} from '../api/api.js'

const ROW_HEIGHT = 48
const TOOLBAR_HEIGHT = 44
const TITLE_HEIGHT = 44
const MIN_ROWS = 2

const modules = ref([])
const currentModuleId = ref(null)
const showAddModule = ref(false)
const newModuleName = ref('')
const showRenameModule = ref(false)
const renameValue = ref('')
const todayTaskRef = ref(null)
const todoPoolRef = ref(null)

const todayMinHeight = computed(() => {
  const count = todayTaskRef.value?.taskList?.length || 0
  const rows = Math.max(count, MIN_ROWS)
  return (rows * ROW_HEIGHT + TOOLBAR_HEIGHT + TITLE_HEIGHT) + 'px'
})

const todoMinHeight = computed(() => {
  const count = todoPoolRef.value?.taskList?.length || 0
  const rows = Math.max(count, MIN_ROWS)
  return (rows * ROW_HEIGHT + TOOLBAR_HEIGHT + TITLE_HEIGHT) + 'px'
})

const todayCount = computed(() => todayTaskRef.value?.taskList?.length || 0)
const todoCount = computed(() => todoPoolRef.value?.taskList?.length || 0)

const handleCopyToClipboard = async () => {
  const todayList = todayTaskRef.value?.taskList || []
  const todoList = todoPoolRef.value?.taskList || []
  if (todayList.length === 0 && todoList.length === 0) {
    ElMessage.warning('暂无任务可复制')
    return
  }
  const mod = modules.value.find(m => m.id === currentModuleId.value)
  let text = `【${mod?.name || ''}】\n\n`
  if (todayList.length > 0) {
    text += '=== 今日任务 ===\n'
    todayList.forEach((item, idx) => {
      text += `${idx + 1}. ${item.content}`
      if (item.remarks) text += `（${item.remarks}）`
      text += '\n'
    })
    text += '\n'
  }
  if (todoList.length > 0) {
    text += '=== 待办任务 ===\n'
    todoList.forEach((item, idx) => {
      const postpone = item.postpone_tomorrow ? ' [明天]' : ''
      text += `${idx + 1}. ${item.content}${postpone}`
      if (item.remarks) text += `（${item.remarks}）`
      text += '\n'
    })
  }
  try {
    await navigator.clipboard.writeText(text.trim())
    ElMessage.success('已复制到剪贴板')
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text.trim()
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  }
}

const onMovedToTodo = () => {
  todoPoolRef.value?.loadTasks()
}

const onMovedToToday = () => {
  todayTaskRef.value?.loadTasks()
}

const loadModules = async () => {
  try {
    modules.value = await getTaskModules()
    if (modules.value.length > 0 && !currentModuleId.value) {
      currentModuleId.value = modules.value[0].id
    }
  } catch (e) {
    ElMessage.error('加载任务模块失败')
  }
}

const selectModule = (id) => {
  currentModuleId.value = id
}

const handleAddModule = async () => {
  if (!newModuleName.value.trim()) {
    ElMessage.warning('请输入模块名称')
    return
  }
  try {
    await createTaskModule({ name: newModuleName.value.trim() })
    ElMessage.success('创建成功')
    showAddModule.value = false
    newModuleName.value = ''
    await loadModules()
    if (modules.value.length > 0) {
      currentModuleId.value = modules.value[modules.value.length - 1].id
    }
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

const handleDeleteModule = async (mod) => {
  try {
    await ElMessageBox.confirm(`确定删除任务模块"${mod.name}"？该模块下所有任务将一并删除。`, '删除确认', {
      type: 'warning'
    })
    await deleteTaskModule(mod.id)
    ElMessage.success('删除成功')
    await loadModules()
    if (currentModuleId.value === mod.id) {
      currentModuleId.value = modules.value.length > 0 ? modules.value[0].id : null
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleEditModule = () => {
  const mod = modules.value.find(m => m.id === currentModuleId.value)
  if (mod) {
    renameValue.value = mod.name
    showRenameModule.value = true
  }
}

const handleRenameModule = async () => {
  if (!renameValue.value.trim()) {
    ElMessage.warning('请输入新名称')
    return
  }
  try {
    await updateTaskModule(currentModuleId.value, { name: renameValue.value.trim() })
    ElMessage.success('重命名成功')
    showRenameModule.value = false
    await loadModules()
  } catch (e) {
    ElMessage.error('重命名失败')
  }
}

onMounted(async () => {
  try {
    await checkPostpone()
  } catch (e) { /* 忽略 */ }
  await loadModules()
})
</script>

<style scoped>
.requirement-summary {
  max-width: 100%;
  overflow-x: hidden;
  background:
    radial-gradient(ellipse 800px 600px at 15% 20%, oklch(96% 0.005 250 / 0.6), transparent 60%),
    radial-gradient(ellipse 700px 500px at 85% 15%, oklch(90% 0.06 200 / 0.5), transparent 55%),
    radial-gradient(ellipse 600px 400px at 10% 80%, oklch(94% 0.05 85 / 0.4), transparent 50%),
    radial-gradient(ellipse 500px 500px at 90% 85%, oklch(93% 0.04 280 / 0.3), transparent 55%),
    radial-gradient(circle 400px at 50% 50%, oklch(96% 0.04 165 / 0.3), transparent 70%),
    oklch(98% 0.01 165);
  background-attachment: fixed;
}
.requirement-body {
  max-width: 1480px;
  margin: 0 auto;
  padding: 48px 24px 24px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  position: relative;
}
.page-header-center {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.page-title {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  font-family: 'Noto Serif SC', 'SimSun', 'STSong', serif;
  letter-spacing: 0.04em;
  background: linear-gradient(135deg, oklch(72% 0.15 165) 0%, oklch(92% 0.08 165) 35%, oklch(82% 0.12 165) 70%, oklch(92% 0.08 165) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 2px 8px oklch(72% 0.15 165 / 0.25));
  position: relative;
}
.page-title::before {
  content: '';
  position: absolute;
  inset: -20px -40px;
  background: radial-gradient(ellipse, oklch(92% 0.08 165 / 0.3), transparent 70%);
  z-index: -1;
  filter: blur(20px);
  pointer-events: none;
}
.page-title::after {
  content: 'Android';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.65) 0%, transparent 50%, rgba(255,255,255,0.2) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  pointer-events: none;
}
.page-header-right {
  position: absolute;
  right: 0;
  display: flex;
  gap: 8px;
}
.module-bar {
  margin-bottom: 28px;
}
.module-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.module-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: 12px;
  background: oklch(99% 0.005 165 / 0.6);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid oklch(100% 0 0 / 0.45);
  cursor: pointer;
  transition: all 0.25s ease;
  font-size: 13px;
  color: oklch(50% 0.04 165);
  box-shadow: 0 1px 3px oklch(72% 0.15 165 / 0.06), inset 0 1px 0 oklch(100% 0 0 / 0.5);
  position: relative;
  overflow: hidden;
}
.module-tab::before {
  content: '';
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, oklch(100% 0 0 / 0.8), transparent);
  pointer-events: none;
}
.module-tab:hover {
  border-color: oklch(72% 0.15 165 / 0.35);
  background: oklch(99% 0.005 165 / 0.8);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  color: oklch(35% 0.03 165);
  box-shadow: 0 4px 12px oklch(72% 0.15 165 / 0.1), inset 0 1px 0 oklch(100% 0 0 / 0.6);
}
.module-tab.active {
  background: oklch(72% 0.15 165 / 0.12);
  border-color: oklch(72% 0.15 165 / 0.4);
  color: oklch(55% 0.12 165);
  box-shadow: 0 2px 8px oklch(72% 0.15 165 / 0.12), inset 0 1px 0 oklch(100% 0 0 / 0.5), inset 0 -1px 0 oklch(72% 0.15 165 / 0.08);
}
.module-tab.active .module-tab-close {
  color: oklch(55% 0.12 165 / 0.6);
}
.module-tab-close {
  font-size: 14px;
  color: oklch(70% 0.02 165);
  transition: color 0.15s;
  cursor: pointer;
}
.module-tab-close:hover {
  color: #C47070;
}
.task-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.task-section {
  position: relative;
  background: oklch(99% 0.005 165 / 0.55);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 14px;
  border: 1px solid oklch(100% 0 0 / 0.5);
  padding: 20px 24px;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
  box-shadow: 0 4px 16px oklch(72% 0.15 165 / 0.08), 0 1px 3px oklch(0% 0 0 / 0.04), inset 0 1px 0 oklch(100% 0 0 / 0.6), inset 0 -1px 0 oklch(72% 0.15 165 / 0.06);
  overflow: hidden;
}
.task-section::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.4 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity: 0.35;
  mix-blend-mode: overlay;
  pointer-events: none;
  z-index: 0;
}
.task-section > * {
  position: relative;
  z-index: 1;
}
.task-section:hover {
  border-color: oklch(100% 0 0 / 0.65);
  box-shadow: 0 8px 24px oklch(72% 0.15 165 / 0.12), 0 2px 6px oklch(0% 0 0 / 0.05), inset 0 1px 0 oklch(100% 0 0 / 0.7), inset 0 -1px 0 oklch(72% 0.15 165 / 0.08);
}
.section-header {
  margin-bottom: 18px;
}
.section-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
.section-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.today-dot {
  background: radial-gradient(circle at 30% 30%, #A8E6D9, #5BBA8A 70%);
  box-shadow: 0 0 8px rgba(91, 186, 138, 0.4), 0 1px 2px rgba(0, 0, 0, 0.08);
}
.todo-dot {
  background: radial-gradient(circle at 30% 30%, #E0D4A8, #C2A86A 70%);
  box-shadow: 0 0 8px rgba(194, 168, 106, 0.4), 0 1px 2px rgba(0, 0, 0, 0.08);
}
.section-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #3D4A3E;
  letter-spacing: 0.02em;
}
.section-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.04);
  font-size: 13px;
  font-weight: 600;
  color: #666;
}
.empty-area {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  overflow: hidden;
  background: #FDFCF8;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.empty-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(156, 175, 136, 0.04) 0%,
    rgba(181, 201, 168, 0.02) 25%,
    rgba(212, 197, 169, 0.04) 50%,
    rgba(181, 201, 168, 0.02) 75%,
    rgba(156, 175, 136, 0.04) 100%
  );
  background-size: 400% 400%;
  animation: gradientShift 8s ease infinite;
}
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
</style>
