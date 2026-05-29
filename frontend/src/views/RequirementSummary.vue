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
}
.requirement-body {
  max-width: 1200px;
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
  background: linear-gradient(135deg, #7D9B6D 0%, #9CAF88 40%, #B5C9A8 80%, #9CAF88 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 2px 6px rgba(125, 155, 109, 0.2));
  position: relative;
}
.page-title::after {
  content: 'Android';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.45) 0%, transparent 50%, rgba(255,255,255,0.15) 100%);
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
  background: rgba(255, 253, 249, 0.8);
  border: 1px solid rgba(181, 201, 168, 0.25);
  cursor: pointer;
  transition: all 0.25s ease;
  font-size: 13px;
  color: #6B7B6C;
  box-shadow: 0 1px 3px rgba(156, 175, 136, 0.06);
}
.module-tab:hover {
  border-color: rgba(125, 155, 109, 0.4);
  background: rgba(255, 253, 249, 0.95);
  color: #4A5E4B;
  box-shadow: 0 2px 8px rgba(125, 155, 109, 0.1);
}
.module-tab.active {
  background: rgba(91, 141, 239, 0.08);
  border-color: rgba(91, 141, 239, 0.25);
  color: #4A7AE6;
  box-shadow: 0 1px 4px rgba(91, 141, 239, 0.06);
}
.module-tab.active .module-tab-close {
  color: rgba(74, 122, 230, 0.6);
}
.module-tab-close {
  font-size: 12px;
  color: #B5C0A8;
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
  background: #FDFCF8;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  padding: 20px 24px;
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.task-section:hover {
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.06);
  border-color: rgba(0, 0, 0, 0.1);
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
  background: #7D9B6D;
}
.todo-dot {
  background: #C2A86A;
}
.section-title {
  margin: 0;
  font-size: 15px;
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
  font-size: 11px;
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
