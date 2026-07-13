<template>
  <section class="date-roulette-section">
    <div class="date-roulette-inner">
      <div class="crescent-container">
        <svg class="crescent-svg" viewBox="0 0 1200 250" preserveAspectRatio="none">
          <defs>
            <linearGradient id="crescentGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#1a1a1a" />
              <stop offset="100%" stop-color="#0a0a0a" />
            </linearGradient>
            <radialGradient id="moonGlow" cx="50%" cy="0%" r="70%">
              <stop offset="0%" stop-color="rgba(201,169,110,0.08)" />
              <stop offset="100%" stop-color="rgba(201,169,110,0)" />
            </radialGradient>
          </defs>
          <path :d="crescentFillPath" fill="url(#crescentGrad)" />
          <path :d="crescentPath" fill="url(#moonGlow)" />
          <path :d="crescentStroke" fill="none" stroke="rgba(201,169,110,0.15)" stroke-width="0.8" />
        </svg>

        <div class="crescent-content">
          <div class="month-nav">
            <button class="month-arrow" @click="prevMonth">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 18 9 12 15 6"></polyline>
              </svg>
            </button>
            <span class="month-label">{{ monthLabel }}</span>
            <button class="month-arrow" @click="nextMonth">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </button>
          </div>

          <div
            class="date-track"
            ref="trackRef"
            @mousedown="onDragStart"
            @mousemove="onDragMove"
            @mouseup="onDragEnd"
            @mouseleave="onDragEnd"
            @touchstart="onTouchStart"
            @touchmove="onTouchMove"
            @touchend="onDragEnd"
            :class="{ dragging: isDragging }"
          >
            <div
              v-for="(day, index) in days"
              :key="day.dateStr || `placeholder-${index}`"
              class="date-item"
              :class="{
                selected: day.inMonth && selectedDate === day.dateStr,
                today: day.inMonth && day.isToday,
                placeholder: !day.inMonth
              }"
              :style="getDateItemStyle(index)"
              @click="day.inMonth && selectDate(day.dateStr)"
            >
              <template v-if="day.inMonth">
                <span class="date-day">{{ day.day }}</span>
                <span class="date-weekday">{{ day.weekday }}</span>
                <span v-if="selectedDate === day.dateStr" class="date-selected-dot"></span>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'

const VISIBLE_DAYS = 15

function formatDateStr(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth())
const selectedDate = ref(formatDateStr(now))
const trackRef = ref(null)
const isDragging = ref(false)
let dragStartX = 0
let scrollStart = 0

const monthLabel = computed(() => {
  return `${currentYear.value}.${String(currentMonth.value + 1).padStart(2, '0')}`
})

const days = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const today = new Date()

  const selected = new Date(selectedDate.value + 'T00:00:00')
  const half = Math.floor(VISIBLE_DAYS / 2)
  const startDate = new Date(selected)
  startDate.setDate(startDate.getDate() - half)

  const result = []
  for (let i = 0; i < VISIBLE_DAYS; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    const inMonth = date.getFullYear() === year && date.getMonth() === month
    const dateStr = formatDateStr(date)
    result.push({
      day: date.getDate(),
      weekday: weekdays[date.getDay()],
      dateStr,
      inMonth,
      isToday: date.toDateString() === today.toDateString()
    })
  }

  return result
})

const crescentPath = computed(() => {
  const w = 1200
  const h = 250
  const startX = 100
  const endX = 1100
  const topY = 0
  const bottomY = h
  const arcDepth = 230

  return `M 0 ${topY} L ${startX} ${topY} Q ${(startX + endX) / 2} ${arcDepth} ${endX} ${topY} L ${w} ${topY} L ${w} ${bottomY} L 0 ${bottomY} Z`
})

const crescentFillPath = computed(() => {
  const startX = 100
  const endX = 1100
  const arcDepth = 230

  return `M 0 0 L ${startX} 0 Q ${(startX + endX) / 2} ${arcDepth} ${endX} 0 L 1200 0 Z`
})

const crescentStroke = computed(() => {
  return `M 100 0 Q 600 230 1100 0`
})

const getDateItemStyle = (index) => {
  const total = days.value.length
  const centerIndex = total / 2
  const offset = index - centerIndex
  const maxOffset = centerIndex
  const normalizedOffset = offset / maxOffset
  const translateY = (1 - Math.pow(normalizedOffset, 2)) * 40

  return {
    transform: `translateY(${translateY}px)`
  }
}

const prevMonth = () => {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
  selectedDate.value = formatDateStr(new Date(currentYear.value, currentMonth.value, 15))
}

const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
  selectedDate.value = formatDateStr(new Date(currentYear.value, currentMonth.value, 15))
}

const selectDate = (dateStr) => {
  if (!isDragging.value) {
    selectedDate.value = dateStr
  }
}

const onDragStart = (e) => {
  isDragging.value = true
  dragStartX = e.clientX || e.touches?.[0]?.clientX || 0
  scrollStart = trackRef.value?.scrollLeft || 0
}

const onDragMove = (e) => {
  if (!isDragging.value || !trackRef.value) return
  const clientX = e.clientX || e.touches?.[0]?.clientX || 0
  const delta = dragStartX - clientX
  trackRef.value.scrollLeft = scrollStart + delta
}

const onDragEnd = () => {
  isDragging.value = false
}

const onTouchStart = (e) => {
  onDragStart(e)
}

const onTouchMove = (e) => {
  onDragMove(e)
}
</script>

<style scoped>
.date-roulette-section {
  padding: 0;
  position: relative;
  overflow: hidden;
  margin-top: 0;
  background: #ffffff;
}

.date-roulette-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.crescent-container {
  position: relative;
  height: 250px;
  overflow: hidden;
}

.crescent-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.crescent-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0 10%;
}

.month-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  flex-shrink: 0;
}

.month-arrow {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s ease;
}

.month-arrow:hover {
  color: rgba(255, 255, 255, 0.95);
}

.month-label {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 15px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.95);
  letter-spacing: 0.2em;
  user-select: none;
}

.date-track {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  cursor: grab;
  padding: 0px 8px 0;
  transform: rotate(-1deg);
  transform-origin: bottom center;
}

.date-track::-webkit-scrollbar {
  display: none;
}

.date-track.dragging {
  cursor: grabbing;
}

.date-item {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 10px;
  cursor: pointer;
  position: relative;
  transition: color 0.3s ease, transform 0.3s ease;
  user-select: none;
  min-width: 36px;
}

.date-day {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 11px;
  font-weight: 500;
  color: rgba(200, 200, 200, 0.7);
  letter-spacing: 0.06em;
  line-height: 1;
  transition: color 0.3s ease;
}

.date-weekday {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 9px;
  font-weight: 400;
  color: rgba(200, 200, 200, 0.5);
  letter-spacing: 0.04em;
  line-height: 1;
  margin-top: 3px;
  transition: color 0.3s ease;
}

.date-item:hover .date-day {
  color: rgba(220, 220, 220, 0.9);
}

.date-item:hover .date-weekday {
  color: rgba(220, 220, 220, 0.7);
}

.date-item.today .date-day {
  color: rgba(201, 169, 110, 0.9);
}

.date-item.today .date-weekday {
  color: rgba(201, 169, 110, 0.6);
}

.date-item.selected .date-day {
  color: rgba(240, 240, 240, 0.95);
  font-weight: 600;
}

.date-item.selected .date-weekday {
  color: rgba(230, 230, 230, 0.8);
}

.date-item.placeholder {
  cursor: default;
  pointer-events: none;
}

.date-selected-dot {
  position: absolute;
  bottom: -4px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #C9A96E;
  box-shadow: 0 0 6px rgba(201, 169, 110, 0.5);
}

@media (max-width: 768px) {
  .crescent-content {
    padding: 0 5%;
  }

  .date-item {
    padding: 4px 7px;
    min-width: 32px;
  }
}
</style>
