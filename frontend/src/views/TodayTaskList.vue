<template>
  <div class="today-task-list">
    <div class="task-toolbar">
      <el-button type="primary" size="small" :icon="Plus" @click="handleAdd">添加任务</el-button>
    </div>

    <draggable
      v-model="taskList"
      item-key="id"
      :delay="0"
      animation="200"
      @end="onDragEnd"
      class="task-draggable"
    >
      <template #item="{ element, index }">
        <div
          class="task-row"
          :class="{ 'task-completed': element.is_completed }"
        >
          <div class="task-left">
            <el-checkbox
              :model-value="element.is_completed"
              @change="handleToggleComplete(element)"
            />
            <span class="task-order">{{ index + 1 }}</span>
            <span class="task-content" :class="{ 'line-through': element.is_completed }">
              {{ element.content }}
            </span>
            <span v-if="element.remarks" class="task-remarks">{{ element.remarks }}</span>
          </div>
          <div class="task-actions">
            <el-button-group size="small">
              <el-button :icon="Top" @click="handleMoveUp(index)" :disabled="index === 0" text />
              <el-button :icon="Bottom" @click="handleMoveDown(index)" :disabled="index === taskList.length - 1" text />
            </el-button-group>
            <el-button size="small" type="warning" @click="handleMoveToTodo(element)" text>待办</el-button>
            <el-button size="small" :icon="Edit" @click="handleEdit(element)" text />
            <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(element)" text />
          </div>
        </div>
      </template>
    </draggable>

    <div v-if="taskList.length === 0" class="empty-hint">
      <span>暂无今日任务，点击上方按钮添加</span>
    </div>

    <el-dialog v-model="showForm" :title="isEdit ? '编辑任务' : '添加任务'" width="460px" @close="resetForm">
      <el-form :model="form" label-width="72px">
        <el-form-item label="任务内容">
          <el-input v-model="form.content" type="textarea" :rows="3" placeholder="请输入任务内容" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remarks" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, h, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { Plus, Edit, Delete, Top, Bottom } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {
  getTaskItems,
  createTaskItem,
  updateTaskItem,
  deleteTaskItem,
  moveToTodo,
  toggleComplete,
  batchReorder
} from '../api/api.js'

const props = defineProps({
  moduleId: { type: Number, required: true }
})

const emit = defineEmits(['moved-to-todo'])

const taskList = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ content: '', remarks: '' })

const loadTasks = async () => {
  try {
    const data = await getTaskItems({ module: props.moduleId, task_type: 'today' })
    taskList.value = data.sort((a, b) => a.order - b.order)
  } catch (e) {
    ElMessage.error('加载今日任务失败')
  }
}

// 409 冲突统一处理：3 秒倒计时后自动刷新，不给用户选择权
const handleConflict = (error) => {
  if (error?.response?.status !== 409) return false
  const countdown = ref(3)
  const notification = ElNotification({
    title: '任务已被修改',
    message: h(() => h('div', { style: 'font-size: 14px' }, [
      h('p', { style: 'margin: 0 0 6px' }, '该任务已被其他用户修改，请刷新后重试'),
      h('p', { style: 'margin: 0; color: #909399; font-size: 13px' }, `${countdown.value} 秒后自动刷新`)
    ])),
    type: 'warning',
    duration: 0,
    showClose: false,
  })
  const timer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(timer)
      notification.close()
      loadTasks()
    }
  }, 1000)
  return true
}

const renumberAndSave = async () => {
  const items = taskList.value.map((item, index) => ({
    id: item.id,
    order: index + 1,
    version: item.version
  }))
  taskList.value.forEach((item, index) => {
    item.order = index + 1
  })
  try {
    const res = await batchReorder(items)
    // 用后端返回的权威 version 同步本地，避免连续排序时误触发 409
    if (res?.items) {
      taskList.value.forEach(item => {
        const updated = res.items.find(i => i.id === item.id)
        if (updated) item.version = updated.version
      })
    }
  } catch (e) {
    handleConflict(e)
  }
}

const onDragEnd = async () => {
  await renumberAndSave()
}

const handleMoveUp = async (index) => {
  if (index <= 0) return
  const temp = taskList.value[index]
  taskList.value[index] = taskList.value[index - 1]
  taskList.value[index - 1] = temp
  taskList.value = [...taskList.value]
  await renumberAndSave()
}

const handleMoveDown = async (index) => {
  if (index >= taskList.value.length - 1) return
  const temp = taskList.value[index]
  taskList.value[index] = taskList.value[index + 1]
  taskList.value[index + 1] = temp
  taskList.value = [...taskList.value]
  await renumberAndSave()
}

const handleToggleComplete = async (item) => {
  try {
    await toggleComplete(item.id, { version: item.version })
    item.is_completed = !item.is_completed
    item.version += 1
  } catch (e) {
    if (!handleConflict(e)) {
      ElMessage.error('操作失败')
    }
  }
}

const handleMoveToTodo = async (item) => {
  try {
    await moveToTodo(item.id, { version: item.version })
    ElMessage.success('已移回待办')
    await loadTasks()
    emit('moved-to-todo')
  } catch (e) {
    if (!handleConflict(e)) {
      ElMessage.error('操作失败')
    }
  }
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  form.value = { content: '', remarks: '' }
  showForm.value = true
}

const handleEdit = (item) => {
  isEdit.value = true
  editId.value = item.id
  form.value = { content: item.content, remarks: item.remarks }
  showForm.value = true
}

const handleSubmit = async () => {
  if (!form.value.content.trim()) {
    ElMessage.warning('请输入任务内容')
    return
  }
  try {
    if (isEdit.value) {
      const task = taskList.value.find(t => t.id === editId.value)
      await updateTaskItem(editId.value, {
        content: form.value.content.trim(),
        remarks: form.value.remarks.trim(),
        version: task?.version
      })
      ElMessage.success('修改成功')
    } else {
      const maxOrder = taskList.value.length > 0
        ? Math.max(...taskList.value.map(t => t.order))
        : 0
      await createTaskItem({
        module: props.moduleId,
        task_type: 'today',
        content: form.value.content.trim(),
        remarks: form.value.remarks.trim(),
        order: maxOrder + 1
      })
      ElMessage.success('添加成功')
    }
    showForm.value = false
    await loadTasks()
  } catch (e) {
    if (handleConflict(e)) {
      showForm.value = false
    } else {
      ElMessage.error(isEdit.value ? '修改失败' : '添加失败')
    }
  }
}

const handleDelete = async (item) => {
  try {
    await ElMessageBox.confirm('确定删除该任务？', '删除确认', { type: 'warning' })
    await deleteTaskItem(item.id, item.version)
    ElMessage.success('删除成功')
    await loadTasks()
  } catch (e) {
    if (e !== 'cancel') {
      if (!handleConflict(e)) {
        ElMessage.error('删除失败')
      }
    }
  }
}

const resetForm = () => {
  form.value = { content: '', remarks: '' }
}

watch(() => props.moduleId, () => {
  loadTasks()
})

onMounted(() => {
  loadTasks()
})

defineExpose({ loadTasks, taskList })
</script>

<style scoped>
.today-task-list {
}
.task-toolbar {
  margin-bottom: 12px;
}
.task-draggable {
}
.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px 10px 18px;
  margin-bottom: 2px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  border-left: 3px solid rgba(125, 155, 109, 0.25);
  background: #EDF2F0;
  transition: all 0.2s ease;
  cursor: default;
}
.task-row:hover {
  background: #E2E8E5;
  border-left-color: #7D9B6D;
}
.task-completed {
  opacity: 0.45;
}
.task-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.task-order {
  color: #bbb;
  font-weight: 500;
  font-size: 14px;
  min-width: 20px;
  text-align: right;
}
.task-content {
  flex: 1;
  word-break: break-all;
  font-size: 16px;
  color: #1a1a1a;
}
.line-through {
  text-decoration: line-through;
  color: #aaa;
}
.task-remarks {
  font-size: 14px;
  color: #888;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  margin-left: 8px;
  opacity: 0;
  transition: opacity 0.15s ease;
}
.task-row:hover .task-actions {
  opacity: 1;
}
.empty-hint {
  text-align: center;
  padding: 32px 0;
  color: #bbb;
  font-size: 15px;
}
</style>
