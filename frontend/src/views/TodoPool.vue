<template>
  <div class="todo-pool">
    <div class="task-toolbar">
      <el-button type="primary" size="small" :icon="Plus" @click="handleAdd">添加待办</el-button>
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
          :class="{ 'task-postponed': element.postpone_tomorrow }"
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
            <span v-if="element.postpone_tomorrow" class="postpone-badge">明天</span>
          </div>
          <div class="task-actions">
            <el-button size="small" type="primary" @click="handleMoveToToday(element)" text>今日</el-button>
            <el-button
              v-if="!element.postpone_tomorrow"
              size="small"
              @click="handlePostpone(element)"
              text
            >明天</el-button>
            <el-button
              v-else
              size="small"
              type="info"
              @click="handleCancelPostpone(element)"
              text
            >取消</el-button>
            <el-button size="small" :icon="Edit" @click="handleEdit(element)" text />
            <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(element)" text />
          </div>
        </div>
      </template>
    </draggable>

    <div v-if="taskList.length === 0" class="empty-hint">
      <span>暂无待办任务</span>
    </div>

    <el-dialog v-model="showForm" :title="isEdit ? '编辑待办' : '添加待办'" width="460px" @close="resetForm">
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
import { ref, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {
  getTaskItems,
  createTaskItem,
  updateTaskItem,
  deleteTaskItem,
  moveToToday,
  postponeTomorrow,
  cancelPostpone,
  toggleComplete,
  batchReorder
} from '../api/api.js'

const props = defineProps({
  moduleId: { type: Number, required: true }
})

const emit = defineEmits(['moved-to-today'])

const taskList = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ content: '', remarks: '' })

const loadTasks = async () => {
  try {
    const data = await getTaskItems({ module: props.moduleId, task_type: 'todo' })
    taskList.value = data.sort((a, b) => a.order - b.order)
  } catch (e) {
    ElMessage.error('加载待办任务失败')
  }
}

const renumberAndSave = async () => {
  const items = taskList.value.map((item, index) => ({
    id: item.id,
    order: index + 1
  }))
  taskList.value.forEach((item, index) => {
    item.order = index + 1
  })
  try {
    await batchReorder(items)
  } catch (e) { /* 忽略 */ }
}

const onDragEnd = async () => {
  await renumberAndSave()
}

const handleToggleComplete = async (item) => {
  try {
    await toggleComplete(item.id)
    item.is_completed = !item.is_completed
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleMoveToToday = async (item) => {
  try {
    await moveToToday(item.id)
    ElMessage.success('已设为今日任务')
    await loadTasks()
    emit('moved-to-today')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handlePostpone = async (item) => {
  try {
    await postponeTomorrow(item.id)
    item.postpone_tomorrow = true
    ElMessage.success('已标记为明天')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleCancelPostpone = async (item) => {
  try {
    await cancelPostpone(item.id)
    item.postpone_tomorrow = false
    ElMessage.success('已取消明天标记')
  } catch (e) {
    ElMessage.error('操作失败')
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
      await updateTaskItem(editId.value, {
        content: form.value.content.trim(),
        remarks: form.value.remarks.trim()
      })
      ElMessage.success('修改成功')
    } else {
      await createTaskItem({
        module: props.moduleId,
        task_type: 'todo',
        content: form.value.content.trim(),
        remarks: form.value.remarks.trim(),
        order: 0
      })
      ElMessage.success('添加成功')
    }
    showForm.value = false
    await loadTasks()
  } catch (e) {
    ElMessage.error(isEdit.value ? '修改失败' : '添加失败')
  }
}

const handleDelete = async (item) => {
  try {
    await ElMessageBox.confirm('确定删除该任务？', '删除确认', { type: 'warning' })
    await deleteTaskItem(item.id)
    ElMessage.success('删除成功')
    await loadTasks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
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
.todo-pool {
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
  border-left: 3px solid rgba(194, 168, 106, 0.25);
  background: #EDF2F0;
  transition: all 0.2s ease;
  cursor: default;
}
.task-row:hover {
  background: #E2E8E5;
  border-left-color: #C2A86A;
}
.task-postponed {
  border-left-color: rgba(194, 168, 106, 0.5);
  background: #F5F0E8;
}
.task-postponed:hover {
  background: #EDE7DB;
  border-left-color: #B8963A;
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
.postpone-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(194, 168, 106, 0.1);
  color: #8A7A5A;
  font-size: 13px;
  font-weight: 500;
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
