<template>
  <section class="concert-section">
    <div class="concert-inner">
      <div class="concert-header">
        <h2 class="concert-title">历 史 记 录</h2>
        <p class="concert-subtitle">HISTORY RECORDS</p>
      </div>

      <div v-if="!dbAvailable" class="history-fallback">
        <p>浏览器不支持 IndexedDB，历史记录功能不可用</p>
      </div>

      <div v-else class="history-workspace">
        <div class="history-toolbar">
          <button class="history-btn" @click="manualSaveAll" :disabled="isSaving">
            {{ isSaving ? '保存中...' : '立即保存' }}
          </button>
          <span class="history-status">自动保存时间：11:00 / 23:00</span>
          <span class="history-status">上次保存：{{ lastSaveTime || '暂无' }}</span>
          <div class="countdown-roller">
            <span class="countdown-label">下次保存</span>
            <div class="roller-group">
              <div class="roller-digit">
                <div class="roller-strip" :style="{ transform: `translateY(-${countdownHours * 40}px)` }">
                  <span v-for="h in 10" :key="'h'+h" class="roller-num">{{ String(h - 1).padStart(2, '0') }}</span>
                </div>
              </div>
              <span class="roller-sep">:</span>
              <div class="roller-digit">
                <div class="roller-strip" :style="{ transform: `translateY(-${countdownMinutes * 40}px)` }">
                  <span v-for="m in 60" :key="'m'+m" class="roller-num">{{ String(m - 1).padStart(2, '0') }}</span>
                </div>
              </div>
              <span class="roller-sep">:</span>
              <div class="roller-digit">
                <div class="roller-strip" :style="{ transform: `translateY(-${countdownSeconds * 40}px)` }">
                  <span v-for="s in 60" :key="'s'+s" class="roller-num">{{ String(s - 1).padStart(2, '0') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="history-panels">
          <div
            v-for="mod in moduleData"
            :key="mod.name"
            class="history-panel"
          >
            <div class="panel-header">
              <h3 class="panel-title">{{ mod.name }}</h3>
              <span class="panel-count">共{{ mod.dates.length }}天</span>
            </div>

            <div class="panel-list">
              <div
                v-for="dateGroup in mod.dates"
                :key="dateGroup.date"
                class="record-item"
                :class="{ active: selectedDate === dateGroup.date && selectedModule === mod.name }"
                @click="selectDate(mod.name, dateGroup)"
              >
                <div class="record-date">{{ dateGroup.date }}</div>
                <div class="record-count">{{ dateGroup.count }}条记录</div>
              </div>
              <div v-if="mod.dates.length === 0" class="record-empty">
                暂无历史记录
              </div>
            </div>
          </div>

          <div v-if="moduleData.length === 0" class="history-empty-all">
            暂无模块数据，请先创建任务模块
          </div>
        </div>

        <div v-if="selectedRecord" class="history-detail">
          <div class="detail-header">
            <h4 class="detail-title">
              {{ selectedRecord.moduleName }} - {{ formatDate(selectedRecord.savedAt) }}
            </h4>
            <button class="detail-close" @click="selectedRecord = null">✕</button>
          </div>
          <div class="detail-body">
            <table class="detail-table">
              <tbody>
                <tr v-for="(line, idx) in detailLines" :key="idx">
                  <td class="line-num">{{ idx + 1 }}</td>
                  <td class="line-content">{{ line }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getTaskModules, getTaskItems } from '../api/api.js'
import {
  saveRecord,
  getRecordsByModule,
  getLastRecordHash,
  simpleHash,
  isIndexedDBAvailable
} from '../utils/historyDB.js'

const dbAvailable = ref(isIndexedDBAvailable())
const isSaving = ref(false)
const lastSaveTime = ref('')
const moduleData = ref([])
const selectedRecord = ref(null)
const selectedDate = ref(null)
const selectedModule = ref(null)
let autoTimer = null
let countdownTimer = null
let calibrationTimer = null
const countdownHours = ref(0)
const countdownMinutes = ref(0)
const countdownSeconds = ref(0)
const lastSaveTimestamp = ref(0)

const SAVE_HOURS = [11, 23]

function getNextSaveTime() {
  const now = new Date()
  for (const h of SAVE_HOURS) {
    const target = new Date(now)
    target.setHours(h, 0, 0, 0)
    if (target > now) return target.getTime()
  }
  const tomorrow = new Date(now)
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(SAVE_HOURS[0], 0, 0, 0)
  return tomorrow.getTime()
}

function updateCountdown() {
  const now = Date.now()
  const nextSave = getNextSaveTime()
  const remaining = Math.max(0, nextSave - now)
  const totalSec = Math.floor(remaining / 1000)
  countdownHours.value = Math.floor(totalSec / 3600)
  countdownMinutes.value = Math.floor((totalSec % 3600) / 60)
  countdownSeconds.value = totalSec % 60
  if (remaining <= 0) {
    saveAllModules()
    lastSaveTimestamp.value = Date.now()
  }
}

function calibrateAndSchedule() {
  const now = new Date()
  const currentHour = now.getHours()
  const currentMinute = now.getMinutes()
  const currentSecond = now.getSeconds()
  const currentMs = now.getMilliseconds()

  if (SAVE_HOURS.includes(currentHour) && currentMinute === 0 && currentSecond === 0) {
    saveAllModules()
    lastSaveTimestamp.value = Date.now()
  }

  let msToNextMinute = (60 - currentSecond) * 1000 - currentMs
  if (msToNextMinute <= 0) msToNextMinute = 60000

  if (autoTimer) clearTimeout(autoTimer)
  autoTimer = setTimeout(() => {
    calibrateAndSchedule()
  }, msToNextMinute)
}

const countdownDisplay = computed(() => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(countdownHours.value)}:${pad(countdownMinutes.value)}:${pad(countdownSeconds.value)}`
})

const detailLines = computed(() => {
  if (!selectedRecord.value || !selectedRecord.value.content) return []
  return selectedRecord.value.content.split('\n')
})

function getPreview(content) {
  if (!content) return ''
  const flat = content.replace(/\n/g, ' ')
  return flat.length > 50 ? flat.substring(0, 50) + '...' : flat
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function extractDateStr(isoStr) {
  if (!isoStr) return ''
  return isoStr.split('T')[0].substring(0, 10)
}

function selectDate(moduleName, dateGroup) {
  selectedModule.value = moduleName
  selectedDate.value = dateGroup.date
  selectedRecord.value = dateGroup.latestRecord
}

function selectRecord(record) {
  selectedRecord.value = record
}

async function fetchModuleTasks(moduleId) {
  try {
    const todayData = await getTaskItems({ module: moduleId, task_type: 'today' })
    const todaySorted = todayData.sort((a, b) => a.order - b.order)

    if (todaySorted.length === 0) return ''

    let text = '=== 今日任务 ===\n'
    todaySorted.forEach((item, idx) => {
      let line = `${idx + 1}. ${item.content}`
      if (item.remarks) line += `（${item.remarks}）`
      if (item.is_completed) line += ' [已完成]'
      text += line + '\n'
    })
    return text.trim()
  } catch {
    return ''
  }
}

async function saveAllModules() {
  if (isSaving.value) return
  isSaving.value = true
  try {
    const modules = await getTaskModules()
    for (const mod of modules) {
      const content = await fetchModuleTasks(mod.id)
      if (!content) continue

      const newHash = simpleHash(content)
      const lastHash = await getLastRecordHash(mod.name)

      if (lastHash !== null && lastHash === newHash) continue

      await saveRecord(mod.name, content)
    }
    lastSaveTime.value = formatTime(new Date().toISOString())
    await loadAllRecords()
  } catch (e) {
    console.error('自动保存失败:', e)
  } finally {
    isSaving.value = false
  }
}

const manualSaveAll = saveAllModules

async function loadAllRecords() {
  try {
    const modules = await getTaskModules()
    const result = []
    for (const mod of modules) {
      const records = await getRecordsByModule(mod.name)
      const dateMap = new Map()
      for (const record of records) {
        const dateKey = extractDateStr(record.savedAt)
        if (!dateMap.has(dateKey)) {
          dateMap.set(dateKey, [])
        }
        dateMap.get(dateKey).push(record)
      }
      const dates = []
      for (const [date, recs] of dateMap) {
        const sorted = recs.sort((a, b) => new Date(b.savedAt) - new Date(a.savedAt))
        dates.push({
          date,
          count: recs.length,
          latestRecord: sorted[0]
        })
      }
      dates.sort((a, b) => b.date.localeCompare(a.date))
      result.push({
        name: mod.name,
        dates
      })
    }
    moduleData.value = result
  } catch (e) {
    console.error('加载历史记录失败:', e)
  }
}

onMounted(async () => {
  await loadAllRecords()
  lastSaveTimestamp.value = Date.now()
  updateCountdown()
  countdownTimer = setInterval(updateCountdown, 1000)
  calibrateAndSchedule()
})

onUnmounted(() => {
  if (autoTimer) {
    clearTimeout(autoTimer)
    autoTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<style scoped>
.concert-section {
  background: #ffffff;
  padding: 0 24px 80px;
  margin-top: -100px;
}

.concert-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.concert-header {
  text-align: center;
  margin-bottom: 48px;
}

.concert-title {
  font-family: 'Noto Serif SC', 'SimSun', 'STSong', serif;
  font-size: 2.25rem;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: 0.25em;
  margin: 0 0 8px;
}

.concert-subtitle {
  font-family: 'Noto Sans SC', -apple-system, sans-serif;
  font-size: 13px;
  font-weight: 300;
  color: #C9A96E;
  letter-spacing: 0.35em;
  margin: 0;
  text-transform: uppercase;
}

.history-fallback {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px dashed #ddd;
}

.history-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #eee;
}

.history-btn {
  padding: 6px 18px;
  border: 1px solid #C9A96E;
  border-radius: 6px;
  background: #fff;
  color: #C9A96E;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.history-btn:hover:not(:disabled) {
  background: #C9A96E;
  color: #fff;
}

.history-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.history-status {
  font-size: 12px;
  color: #999;
}

.countdown-roller {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.countdown-label {
  font-size: 11px;
  color: #aaa;
  white-space: nowrap;
}

.roller-group {
  display: flex;
  align-items: center;
  gap: 2px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border-radius: 8px;
  padding: 4px 8px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    inset 0 -1px 0 rgba(0, 0, 0, 0.05),
    0 4px 16px rgba(0, 0, 0, 0.08);
}

.roller-digit {
  width: 36px;
  height: 40px;
  overflow: hidden;
  position: relative;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.roller-digit::before,
.roller-digit::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  height: 8px;
  z-index: 2;
  pointer-events: none;
}

.roller-digit::before {
  top: 0;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.12), transparent);
}

.roller-digit::after {
  bottom: 0;
  background: linear-gradient(to top, rgba(255, 255, 255, 0.12), transparent);
}

.roller-strip {
  transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  will-change: transform;
}

.roller-num {
  display: block;
  height: 40px;
  line-height: 40px;
  text-align: center;
  font-family: 'Courier New', 'Consolas', monospace;
  font-size: 18px;
  font-weight: 700;
  color: #EC7C7C;
  text-shadow: 0 0 8px rgba(236, 124, 124, 0.3);
  user-select: none;
}

.roller-sep {
  font-family: 'Courier New', monospace;
  font-size: 18px;
  font-weight: 700;
  color: #C9A96E;
  text-shadow: 0 0 6px rgba(201, 169, 110, 0.4);
  line-height: 40px;
  animation: sepBlink 1s ease-in-out infinite;
}

@keyframes sepBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.history-panels {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.history-panel {
  flex: 0 0 320px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(135deg, #fafafa, #f5f5f0);
  border-bottom: 1px solid #eee;
}

.panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  letter-spacing: 0.04em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.panel-count {
  flex-shrink: 0;
  font-size: 11px;
  color: #C9A96E;
  background: rgba(201, 169, 110, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.panel-list {
  max-height: 360px;
  overflow-y: auto;
}

.record-item {
  padding: 10px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background 0.2s ease;
}

.record-item:hover {
  background: #fafaf5;
}

.record-item.active {
  background: rgba(201, 169, 110, 0.08);
  border-left: 3px solid #C9A96E;
}

.record-date {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.record-count {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

.record-empty {
  padding: 24px;
  text-align: center;
  color: #ccc;
  font-size: 13px;
}

.history-empty-all {
  padding: 40px;
  text-align: center;
  color: #999;
  font-size: 14px;
  width: 100%;
}

.history-detail {
  margin-top: 24px;
  border: 1px solid #eee;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fafafa, #f5f5f0);
  border-bottom: 1px solid #eee;
}

.detail-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.detail-close {
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: #999;
  font-size: 14px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.detail-close:hover {
  background: #f0f0f0;
  color: #333;
}

.detail-body {
  max-height: 400px;
  overflow: auto;
  background: #fafafa;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Courier New', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.8;
}

.detail-table tr {
  border-bottom: 1px solid #f0f0f0;
}

.detail-table tr:hover {
  background: #f5f5f0;
}

.line-num {
  width: 48px;
  padding: 2px 12px;
  text-align: right;
  color: #bbb;
  user-select: none;
  background: #f5f5f5;
  border-right: 1px solid #eee;
  font-size: 11px;
}

.line-content {
  padding: 2px 16px;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
}

@media (max-width: 768px) {
  .concert-section {
    padding: 64px 16px 56px;
  }

  .history-panels {
    flex-direction: column;
  }

  .history-panel {
    flex: 0 0 auto;
    width: 100%;
  }

  .history-toolbar {
    flex-wrap: wrap;
  }
}
</style>
