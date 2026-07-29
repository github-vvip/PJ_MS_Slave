<template>
  <div
    ref="bannerRef"
    class="hero-banner"
    :class="{ degraded }"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @mousemove="onTrail"
    @click="onWaterClick"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
  >
    <!-- L0+L1 水面层（WebGL） / 降级静态水面 -->
    <WaterCanvas v-if="!degraded" ref="waterRef" @unsupported="onWaterUnsupported" />
    <div v-else class="hero-water-static"></div>

    <!-- L2 轮播层 -->
    <div ref="stageRef" class="hero-stage">
      <div
        v-for="(slide, i) in slides"
        :key="i"
        :ref="el => setSlideRef(el, i)"
        class="hero-slide"
        :class="{ active: i === current, settled: i === current && settledFlag }"
      >
        <div class="slide-bob">
          <img
            class="slide-img"
            :src="slide.image"
            :alt="slide.title"
            draggable="false"
            :fetchpriority="i === 0 ? 'high' : 'auto'"
          />
        </div>
      </div>
    </div>

    <!-- L3 粒子层 -->
    <SplashParticles v-if="!degraded" ref="splashRef" @drop="onDrop" />

    <!-- 左右箭头 -->
    <button class="hero-arrow hero-arrow-left" aria-label="上一张" @click.stop="go(-1)">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>
    <button class="hero-arrow hero-arrow-right" aria-label="下一张" @click.stop="go(1)">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <polyline points="9 6 15 12 9 18" />
      </svg>
    </button>

    <!-- 水滴涟漪指示器 -->
    <div class="hero-indicators">
      <button
        v-for="(slide, i) in slides"
        :key="i"
        class="hero-dot"
        :class="{ active: i === current }"
        :aria-label="slide.title"
        @click.stop="goTo(i)"
      >
        <span v-if="i === current" class="hero-dot-ring"></span>
        <span class="hero-dot-core"></span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import WaterCanvas from '../components/banner/WaterCanvas.vue'
import SplashParticles from '../components/banner/SplashParticles.vue'

// 降级环境检测：prefers-reduced-motion 或 WebGL 不可用（同步执行于 setup）
const detectWebGL = () => {
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl') || c.getContext('experimental-webgl'))
  } catch (e) {
    return false
  }
}
const isDegradedEnv = () =>
  window.matchMedia('(prefers-reduced-motion: reduce)').matches || !detectWebGL()

const slides = [
  { image: '/DBbackup/Photo/ZhiXiang2.png', title: 'ZhiXiang' },
  { image: '/DBbackup/Photo/Frameo.png', title: 'Frameo' }
]

const AUTOPLAY_DELAY = 6000
const TRAIL_THROTTLE = 16 // 波动方程需要连续轨迹输入，约每帧一滴

const bannerRef = ref(null)
const stageRef = ref(null)
const waterRef = ref(null)
const splashRef = ref(null)

const current = ref(0)
const settledFlag = ref(false)
const transitioning = ref(false)
const degraded = ref(isDegradedEnv())
const waterTopCss = ref(216)

// ---- 尺寸状态 ----
let bannerW = 0
let bannerH = 300
let waterH = 84
let hovered = false
let inView = true
let io = null
let roBanner = null
let autoTimer = null
let rainTimer = null
let contactTimer = null
let lastTrail = 0
let lastTrailX = -1
let lastTrailY = -1
let touchX = 0
const imageCache = []
const slideCache = []

// ---------- 工具 ----------
const wait = (ms) => new Promise(r => setTimeout(r, ms))

const loadImage = (src) => new Promise((resolve, reject) => {
  const im = new Image()
  im.onload = () => resolve(im)
  im.onerror = reject
  im.src = src
})

const setSlideRef = (el, i) => {
  if (!el) return
  slideCache[i] = { root: el }
}

// ---------- 布局 ----------
let imgRectCss = null // 图片显示矩形（CSS px，banner 坐标），用于事件排除与涟漪定位

const measure = () => {
  const el = bannerRef.value
  if (!el) return
  bannerW = el.clientWidth
  bannerH = el.clientHeight
  waterH = parseFloat(getComputedStyle(el).getPropertyValue('--water-h')) || 84
  waterTopCss.value = bannerH - waterH
  layoutImageRect()
}

const layoutImageRect = () => {
  const img = imageCache[current.value]
  if (!img || !img.naturalWidth) return
  const stageW = bannerW
  const stageH = bannerH - waterH
  if (stageH <= 0) return
  const ar = img.naturalWidth / img.naturalHeight
  let w, h
  if (ar > stageW / stageH) {
    w = stageW
    h = w / ar
  } else {
    h = stageH
    w = h * ar
  }
  imgRectCss = { x: (stageW - w) / 2, y: stageH - h, w, h }
}

// 坐标是否落在图片区域（图片浮在水上，落在其上的操作不产生水波）
const inImage = (x, y) => {
  const r = imgRectCss
  if (!r) return false
  return x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h
}

// ---------- 调度（自动轮播 / 雨滴）----------
const clearAuto = () => {
  if (autoTimer) {
    clearTimeout(autoTimer)
    autoTimer = null
  }
}

const schedule = () => {
  clearAuto()
  if (hovered || document.hidden || !inView || transitioning.value) return
  autoTimer = setTimeout(() => go(1), AUTOPLAY_DELAY)
}

const clearRain = () => {
  if (rainTimer) {
    clearTimeout(rainTimer)
    rainTimer = null
  }
}

const scheduleRain = () => {
  clearRain()
  if (degraded.value) return
  rainTimer = setTimeout(() => {
    if (!document.hidden && inView && waterRef.value) {
      // 随机落点，避开图片区域（落在图片后的涟漪不可见，直接放弃本次）
      const x = Math.random() * bannerW
      const y = Math.random() * bannerH
      if (!inImage(x, y)) {
        waterRef.value.addDrop(x, y, 5, 0.7 + Math.random() * 0.5)
      }
    }
    scheduleRain()
  }, 4000 + Math.random() * 3000)
}

// ---------- 接触涟漪：图片底边持续被水轻抚 ----------
const clearContact = () => {
  if (contactTimer) {
    clearTimeout(contactTimer)
    contactTimer = null
  }
}

const scheduleContact = () => {
  clearContact()
  if (degraded.value) return
  contactTimer = setTimeout(() => {
    if (!document.hidden && inView && waterRef.value && imgRectCss) {
      const r = imgRectCss
      const x = r.x + r.w * (0.08 + Math.random() * 0.84)
      waterRef.value.addDrop(x, waterTopCss.value + 2, 3.5, 0.22 + Math.random() * 0.18)
    }
    scheduleContact()
  }, 1500 + Math.random() * 1500)
}

const onWake = () => {
  if (document.hidden || !inView) return
  waterRef.value && waterRef.value.resume()
  schedule()
  scheduleRain()
  scheduleContact()
}

const onSleep = () => {
  waterRef.value && waterRef.value.pause()
  clearAuto()
  clearRain()
  clearContact()
}

// ---------- 横屏轮播转场 ----------
const transitionTo = async (idx, dir) => {
  if (transitioning.value || idx === current.value) return
  transitioning.value = true
  settledFlag.value = false
  clearAuto()

  const out = slideCache[current.value]
  const inn = slideCache[idx]

  if (degraded.value) {
    current.value = idx
    await wait(750)
    transitioning.value = false
    settledFlag.value = true
    schedule()
    return
  }

  // 切换泛涟漪：沿图片底边下缘一排扰动，从滑入侧向另一侧扫过
  const water = waterRef.value
  if (water && imgRectCss) {
    const r = imgRectCss
    const n = 12
    for (let i = 0; i < n; i++) {
      const k = dir > 0 ? i / (n - 1) : 1 - i / (n - 1)
      water.addDrop(r.x + r.w * (0.06 + 0.88 * k), waterTopCss.value + 4, 7, 0.7)
    }
  }

  // 撤销 out/inn 元素上残留的上次转场 WAAPI + 清理 inline 样式（commitStyles 残留），避免累积与冲突
  ;[out.root, inn.root].forEach(el => {
    if (el.getAnimations) el.getAnimations().forEach(a => a.cancel())
    el.style.removeProperty('transform')
    el.style.removeProperty('opacity')
    el.style.removeProperty('visibility')
  })

  const anims = []
  const A = (el, kf, opts) => {
    const a = el.animate(kf, { fill: 'forwards', ...opts })
    anims.push(a)
    return a
  }

  try {
    // 旧图滑出，新图滑入，浮牌漂移：Y轴起伏 + 透明度叠加（去掉 rotateZ 避免 cancel 闪烁）
    A(out.root, [
      { transform: 'translateX(0%) translateY(0)', opacity: 1, visibility: 'visible' },
      { transform: `translateX(${-dir * 100}%) translateY(-8px)`, opacity: 0.3, visibility: 'visible' }
    ], { duration: 750, easing: 'cubic-bezier(.25,.9,.32,1)' })
    A(inn.root, [
      { transform: `translateX(${dir * 100}%) translateY(8px)`, opacity: 0.3, visibility: 'visible' },
      { transform: 'translateX(0%) translateY(0)', opacity: 1, visibility: 'visible' }
    ], { duration: 750, easing: 'cubic-bezier(.25,.9,.32,1)' })

    await wait(750)

    // ---- 落定：切换 active，commitStyles 提交终态到 inline 再 cancel，避免 cancel 重绘闪烁 ----
    current.value = idx
    await nextTick()
    anims.forEach(a => {
      try { a.commitStyles() } catch (e) {}
      a.cancel()
    })
    layoutImageRect()
    settledFlag.value = true
  } finally {
    transitioning.value = false
    schedule()
  }
}

const go = (dir) => {
  if (transitioning.value || slides.length < 2) return
  const idx = (current.value + dir + slides.length) % slides.length
  transitionTo(idx, dir)
}

const goTo = (i) => {
  if (transitioning.value || i === current.value) return
  transitionTo(i, i > current.value ? 1 : -1)
}

// ---------- 水面交互 ----------
const onTrail = (e) => {
  if (degraded.value || !waterRef.value) return
  const rect = bannerRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  if (inImage(x, y)) return
  const now = performance.now()
  if (now - lastTrail < TRAIL_THROTTLE) return
  // 力度随鼠标速度：快划起浪，慢划细纹
  let strength = 0.2
  if (lastTrailX >= 0) {
    const dx = x - lastTrailX
    const dy = y - lastTrailY
    const dt = Math.max(now - lastTrail, 1)
    const speed = Math.sqrt(dx * dx + dy * dy) / dt * 1000
    strength = Math.min(0.16 + speed * 0.00045, 0.7)
  }
  lastTrail = now
  lastTrailX = x
  lastTrailY = y
  waterRef.value.addDrop(x, y, 4, strength)
}

const onWaterClick = (e) => {
  if (degraded.value || !waterRef.value) return
  if (e.target.closest('.hero-arrow, .hero-indicators')) return
  const rect = bannerRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  if (inImage(x, y)) return
  waterRef.value.addDrop(x, y, 8, 1.7)
  if (splashRef.value) splashRef.value.splash(x, y, 0, 10)
}

const onDrop = (x, homeY) => {
  if (degraded.value || !waterRef.value) return
  waterRef.value.addDrop(x, homeY + 2, 3, 0.35)
}

const onWaterUnsupported = () => {
  degraded.value = true
}

// ---------- 悬停 / 触摸 ----------
const onEnter = () => {
  hovered = true
  clearAuto()
}

const onLeave = () => {
  hovered = false
  schedule()
}

const onTouchStart = (e) => {
  touchX = e.touches[0].clientX
}

const onTouchEnd = (e) => {
  const dx = e.changedTouches[0].clientX - touchX
  if (Math.abs(dx) > 48) go(dx < 0 ? 1 : -1)
}

// ---------- 生命周期 ----------
const onVis = () => {
  if (document.hidden) onSleep()
  else onWake()
}

onMounted(async () => {
  await nextTick()
  measure()

  roBanner = new ResizeObserver(() => {
    measure()
    if (waterRef.value) waterRef.value.resize()
  })
  roBanner.observe(bannerRef.value)

  io = new IntersectionObserver(([entry]) => {
    inView = entry.isIntersecting
    if (inView) onWake()
    else onSleep()
  }, { threshold: 0.05 })
  io.observe(bannerRef.value)

  document.addEventListener('visibilitychange', onVis)

  if (!degraded.value) {
    try {
      imageCache[0] = await loadImage(slides[0].image)
      layoutImageRect()
    } catch (e) { /* 首图加载失败时涟漪定位降级为全宽 */ }
    loadImage(slides[1].image).then(im => { imageCache[1] = im }).catch(() => {})
  }

  settledFlag.value = true
  requestAnimationFrame(() => {
    const firstSlide = slideCache[0]?.root
    if (firstSlide) firstSlide.classList.add('hero-enter-once')
  })
  schedule()
  scheduleRain()
  scheduleContact()
})

onBeforeUnmount(() => {
  clearAuto()
  clearRain()
  clearContact()
  document.removeEventListener('visibilitychange', onVis)
  if (io) io.disconnect()
  if (roBanner) roBanner.disconnect()
})
</script>

<style scoped>
.hero-banner {
  --water-h: 72px;
  position: relative;
  width: 100%;
  height: 380px;
  overflow: hidden;
  background: #071018;
  margin-bottom: 0;
  isolation: isolate;
}

/* ---- L2 轮播层 ---- */
.hero-stage {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: calc(100% - var(--water-h));
  z-index: 10;
}

.hero-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  visibility: hidden;
  will-change: transform;
}

.hero-slide.active {
  opacity: 1;
  visibility: visible;
}

.slide-bob {
  position: absolute;
  inset: 0;
}

.hero-slide.settled .slide-bob {
  animation: heroBob 6.2s ease-in-out infinite;
}

@keyframes heroBob {
  0%, 100% { transform: translateY(0) rotateZ(0deg); }
  50% { transform: translateY(-5px) rotateZ(0.4deg); }
}

.slide-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: bottom;
  user-select: none;
  -webkit-user-drag: none;
  /* 俯视阳光下的浮牌投影：收敛避免与水面高光冲突 */
  filter: drop-shadow(0 10px 16px rgba(3, 22, 44, 0.4));
  /* 水面倒影：图片下方渐隐镜像，强化"浮在水上" */
  -webkit-box-reflect: below 2px linear-gradient(to bottom, rgba(255,255,255,0.35) 0%, transparent 45%);
}

/* 入场缩放：仅首屏首图加载时触发一次，转场后不重复触发（避免与 WAAPI 终态 opacity 冲突导致闪烁） */
.hero-slide.hero-enter-once .slide-img {
  animation: heroEnter 0.8s ease-out;
}

@keyframes heroEnter {
  from { transform: scale(0.98); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* ---- 降级静态水面（上深下浅海水 + 白点纹理）---- */
.hero-water-static {
  position: absolute;
  inset: 0;
  z-index: 1;
  background:
    radial-gradient(ellipse 90% 70% at 72% 88%, rgba(34, 208, 192, 0.45), transparent 62%),
    linear-gradient(to bottom, #0d4fc0 0%, #1290c8 55%, #22d0c0 100%);
}

.hero-water-static::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.55 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  mix-blend-mode: overlay;
  opacity: 0.5;
}

/* ---- 箭头 ---- */
.hero-arrow {
  position: absolute;
  top: 44%;
  transform: translateY(-50%);
  z-index: 30;
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
  transition: border-color 0.3s ease, color 0.3s ease, background 0.3s ease, box-shadow 0.3s ease;
  backdrop-filter: blur(4px);
}

.hero-arrow::after {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 50%;
  border: 1px solid rgba(201, 169, 110, 0);
  pointer-events: none;
}

.hero-arrow:hover {
  border-color: #c9a96e;
  color: #c9a96e;
  background: rgba(201, 169, 110, 0.08);
  box-shadow: 0 0 20px rgba(201, 169, 110, 0.15);
}

.hero-arrow:hover::after {
  animation: arrowRipple 0.9s ease-out;
}

@keyframes arrowRipple {
  0% { transform: scale(1); border-color: rgba(201, 169, 110, 0.55); opacity: 1; }
  100% { transform: scale(1.65); border-color: rgba(201, 169, 110, 0); opacity: 0; }
}

.hero-arrow-left { left: 32px; }
.hero-arrow-right { right: 32px; }

/* ---- 水滴涟漪指示器 ---- */
.hero-indicators {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 20px;
  z-index: 30;
}

.hero-dot {
  position: relative;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-dot-core {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.32);
  transition: background 0.3s ease, transform 0.3s ease;
}

.hero-dot:hover .hero-dot-core {
  background: rgba(255, 255, 255, 0.6);
}

.hero-dot.active .hero-dot-core {
  background: #c9a96e;
  transform: scale(1.15);
  box-shadow: 0 0 8px rgba(201, 169, 110, 0.55);
}

.hero-dot-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(201, 169, 110, 0.7);
  animation: dotRing 2s ease-out infinite;
  pointer-events: none;
}

@keyframes dotRing {
  0% { transform: scale(0.45); opacity: 0.9; }
  100% { transform: scale(1.25); opacity: 0; }
}

/* ---- 降级模式：交叉淡入淡出 ---- */
.degraded .hero-slide {
  transition: opacity 0.6s ease, visibility 0s linear 0.6s;
  will-change: opacity;
}

.degraded .hero-slide.active {
  transition: opacity 0.6s ease;
}

.degraded .hero-slide.settled .slide-bob {
  animation: none;
}

/* ---- 响应式 ---- */
@media (max-width: 640px) {
  .hero-banner {
    --water-h: 56px;
    height: 260px;
  }
  .hero-arrow {
    width: 38px;
    height: 38px;
  }
  .hero-arrow-left { left: 12px; }
  .hero-arrow-right { right: 12px; }
  .hero-indicators { bottom: 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .hero-slide.settled .slide-bob {
    animation: none;
  }
  .hero-dot-ring {
    animation: none;
  }
  .hero-arrow:hover::after {
    animation: none;
  }
}
</style>
