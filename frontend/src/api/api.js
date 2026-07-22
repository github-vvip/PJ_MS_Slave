/**
 * API 请求封装
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

/* ========== 任务模块 API ========== */

export const getTaskModules = () => api.get('/task-modules/')

export const createTaskModule = (data) => api.post('/task-modules/', data)

export const updateTaskModule = (id, data) => api.patch(`/task-modules/${id}/`, data)

export const deleteTaskModule = (id) => api.delete(`/task-modules/${id}/`)

/* ========== 任务项 API ========== */

export const getTaskItems = (params) => api.get('/task-items/', { params })

export const createTaskItem = (data) => api.post('/task-items/', data)

export const updateTaskItem = (id, data) => api.patch(`/task-items/${id}/`, data)

export const deleteTaskItem = (id, version) => api.delete(`/task-items/${id}/`, version != null ? { params: { version } } : undefined)

export const moveToTodo = (id, data = {}) => api.post(`/task-items/${id}/move-to-todo/`, data)

export const moveToToday = (id, data = {}) => api.post(`/task-items/${id}/move-to-today/`, data)

export const postponeTomorrow = (id, data = {}) => api.post(`/task-items/${id}/postpone-tomorrow/`, data)

export const cancelPostpone = (id, data = {}) => api.post(`/task-items/${id}/cancel-postpone/`, data)

export const toggleComplete = (id, data = {}) => api.post(`/task-items/${id}/toggle-complete/`, data)

export const batchReorder = (items) => api.post('/task-items/batch-reorder/', { items })

export const checkPostpone = () => api.post('/task-items/check-postpone/')

/* ========== 客户 API ========== */

export const getCustomers = () => api.get('/customers/')

export const createCustomer = (data) => api.post('/customers/', data)

export const updateCustomer = (id, data) => api.patch(`/customers/${id}/`, data)

export const deleteCustomer = (id) => api.delete(`/customers/${id}/`)

/* ========== 项目配置 API ========== */

export const getProjects = (params) => api.get('/projects/', { params })

export const createProject = (data) => api.post('/projects/', data)

export const updateProject = (id, data) => api.patch(`/projects/${id}/`, data)

export const deleteProject = (id) => api.delete(`/projects/${id}/`)

export const getProjectFilterOptions = (params) => api.get('/projects/filter-options/', { params })

export const batchImportProjects = (data) => api.post('/projects/batch-import/', data)

/* ========== 配置雷达 API ========== */

export const searchProjects = () => api.post('/search/')

/* ========== 历史快照 API ========== */

export const getHistorySnapshots = (params) => api.get('/history-snapshots/', { params })

export const saveHistorySnapshot = (data) => api.post('/history-snapshots/save-snapshot/', data)

export const saveAllHistorySnapshots = () => api.post('/history-snapshots/save-all-snapshots/')

export const deleteHistorySnapshot = (id) => api.delete(`/history-snapshots/${id}/`)

/* ========== 数据同步 API ========== */

export const executeDataSync = (onLog, onComplete, onError) => {
  fetch('/api/data-sync/execute/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          try {
            const data = JSON.parse(dataStr)
            if (currentEvent === 'log') {
              onLog(data)
            } else if (currentEvent === 'complete') {
              onComplete(data)
            }
          } catch (e) {
            // JSON 解析失败则忽略
          }
        }
      }
    }
  }).catch((err) => {
    onError(err.message || '同步请求失败')
  })
}

export default api
