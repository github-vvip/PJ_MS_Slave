<template>
  <div class="hero-banner" @mouseenter="pause" @mouseleave="resume">
    <div class="hero-slides">
      <div
        v-for="(slide, index) in slides"
        :key="index"
        class="hero-slide"
        :class="{ active: currentIndex === index, leaving: leavingIndex === index }"
      >
        <img
          :src="slide.image"
          :srcset="`${slide.image} 600w`"
          sizes="(max-width: 640px) 300px, (max-width: 1024px) 500px, 600px"
          :alt="slide.title"
          class="hero-slide-img"
          loading="eager"
        />
        <div class="hero-overlay"></div>
      </div>
    </div>

    <button class="hero-arrow hero-arrow-left" @click="prev">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>
    <button class="hero-arrow hero-arrow-right" @click="next">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <polyline points="9 6 15 12 9 18" />
      </svg>
    </button>

    <div class="hero-indicators">
      <div
        v-for="(slide, index) in slides"
        :key="index"
        class="hero-indicator"
        :class="{ active: currentIndex === index }"
        @click="goTo(index)"
      >
        <div class="hero-indicator-fill" :style="indicatorStyle(index)"></div>
      </div>
    </div>

    <div class="hero-scroll-hint">
      <div class="hero-scroll-line"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const slides = [
  { image: '/DBbackup/Photo/ZhiXiang2.png' },
  { image: '/DBbackup/Photo/Frameo.png' }
]

const currentIndex = ref(0)
const leavingIndex = ref(-1)
const isPaused = ref(false)
const progress = ref(0)
const DURATION = 6000
let timer = null
let progressTimer = null
let progressStart = 0

const indicatorStyle = (index) => {
  if (index === currentIndex.value) {
    return { width: progress.value + '%' }
  }
  return { width: '0%' }
}

const startProgress = () => {
  progressStart = Date.now()
  progress.value = 0
  clearInterval(progressTimer)
  progressTimer = setInterval(() => {
    const elapsed = Date.now() - progressStart
    progress.value = Math.min((elapsed / DURATION) * 100, 100)
  }, 30)
}

const stopProgress = () => {
  clearInterval(progressTimer)
}

const next = () => {
  leavingIndex.value = currentIndex.value
  currentIndex.value = (currentIndex.value + 1) % slides.length
  startProgress()
  setTimeout(() => { leavingIndex.value = -1 }, 800)
}

const prev = () => {
  leavingIndex.value = currentIndex.value
  currentIndex.value = (currentIndex.value - 1 + slides.length) % slides.length
  startProgress()
  setTimeout(() => { leavingIndex.value = -1 }, 800)
}

const goTo = (index) => {
  if (index === currentIndex.value) return
  leavingIndex.value = currentIndex.value
  currentIndex.value = index
  startProgress()
  setTimeout(() => { leavingIndex.value = -1 }, 800)
}

const pause = () => {
  isPaused.value = true
  clearInterval(timer)
  stopProgress()
}

const resume = () => {
  isPaused.value = false
  startProgress()
  clearInterval(timer)
  timer = setInterval(() => {
    next()
  }, DURATION)
}

onMounted(() => {
  startProgress()
  timer = setInterval(() => {
    next()
  }, DURATION)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  clearInterval(progressTimer)
})
</script>

<style scoped>
.hero-banner {
  position: relative;
  width: 100%;
  height: 300px;
  overflow: hidden;
  background: #0a0a0a;
  margin-bottom: 0;
}

.hero-slides {
  position: relative;
  width: 100%;
  height: 100%;
}

.hero-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.8s ease;
  z-index: 1;
}

.hero-slide.active {
  opacity: 1;
  z-index: 2;
}

.hero-slide.leaving {
  opacity: 0;
  z-index: 2;
  transition: opacity 0.8s ease;
}

.hero-slide-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.15) 0%,
    rgba(0, 0, 0, 0.05) 40%,
    rgba(0, 0, 0, 0.4) 100%
  );
  z-index: 1;
}

.hero-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 48px;
  height: 48px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 50%;
  background: transparent;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  backdrop-filter: blur(4px);
}

.hero-arrow:hover {
  border-color: #c9a96e;
  color: #c9a96e;
  background: rgba(201, 169, 110, 0.08);
  box-shadow: 0 0 20px rgba(201, 169, 110, 0.15);
}

.hero-arrow-left {
  left: 32px;
}

.hero-arrow-right {
  right: 32px;
}

.hero-indicators {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 24px;
  z-index: 10;
}

.hero-indicator {
  width: 48px;
  height: 2px;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  overflow: hidden;
  transition: background 0.3s ease;
  border-radius: 1px;
}

.hero-indicator:hover {
  background: rgba(255, 255, 255, 0.35);
}

.hero-indicator.active {
  background: rgba(255, 255, 255, 0.2);
}

.hero-indicator-fill {
  height: 100%;
  background: #c9a96e;
  border-radius: 1px;
  transition: width 0.05s linear;
}

.hero-scroll-hint {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.hero-scroll-line {
  width: 1px;
  height: 32px;
  background: linear-gradient(to bottom, transparent, rgba(201, 169, 110, 0.6));
  animation: scrollPulse 2s ease-in-out infinite;
}

@keyframes scrollPulse {
  0%, 100% {
    opacity: 0.4;
    transform: scaleY(0.6);
    transform-origin: top;
  }
  50% {
    opacity: 1;
    transform: scaleY(1);
    transform-origin: top;
  }
}
</style>
