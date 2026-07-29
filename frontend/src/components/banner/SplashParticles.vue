<template>
  <canvas ref="canvasRef" class="splash-canvas" aria-hidden="true"></canvas>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits(['drop'])

const MAX_PARTICLES = 60
const GRAVITY = 980

const canvasRef = ref(null)
let ctx = null
let dpr = 1
let raf = 0
let lastTs = 0
let ro = null
const pool = []

const alloc = () => {
  for (const p of pool) {
    if (!p.active) return p
  }
  if (pool.length < MAX_PARTICLES) {
    const p = { active: false, x: 0, y: 0, vx: 0, vy: 0, r: 2, life: 0, maxLife: 1, homeY: 0 }
    pool.push(p)
    return p
  }
  return null
}

// dir: -1 左偏 / 0 居中 / 1 右偏；count 单次封顶 30；y 即粒子的水平面（落回判定线）
const splash = (x, y, dir = 0, count = 22) => {
  const n = Math.min(count, 30)
  for (let i = 0; i < n; i++) {
    const p = alloc()
    if (!p) break
    const ang = -Math.PI / 2 + (Math.random() - 0.5) * 1.5 + dir * 0.35
    const speed = 130 + Math.random() * 220
    p.active = true
    p.x = x + (Math.random() - 0.5) * 14
    p.y = y
    p.homeY = y
    p.vx = Math.cos(ang) * speed + dir * 60
    p.vy = Math.sin(ang) * speed
    p.r = 0.9 + Math.random() * 2.1
    p.life = 0
    p.maxLife = 0.55 + Math.random() * 0.55
  }
  startLoop()
}

const startLoop = () => {
  if (raf) return
  lastTs = performance.now()
  raf = requestAnimationFrame(tick)
}

const tick = (ts) => {
  raf = 0
  const dt = Math.min((ts - lastTs) / 1000, 0.05)
  lastTs = ts
  let alive = 0

  ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  ctx.globalCompositeOperation = 'lighter'

  for (const p of pool) {
    if (!p.active) continue
    p.life += dt
    p.vy += GRAVITY * dt
    p.x += p.vx * dt
    p.y += p.vy * dt
    if (p.life >= p.maxLife || (p.vy > 0 && p.y > p.homeY)) {
      p.active = false
      if (p.y > p.homeY - 4) emit('drop', p.x, p.homeY)
      continue
    }
    alive++
    const t = p.life / p.maxLife
    const alpha = (1 - t) * 0.85
    const r = p.r * (1 - t * 0.4) * dpr
    const g = ctx.createRadialGradient(p.x * dpr, p.y * dpr, 0, p.x * dpr, p.y * dpr, r * 2.2)
    g.addColorStop(0, `rgba(235, 248, 252, ${alpha})`)
    g.addColorStop(1, 'rgba(235, 248, 252, 0)')
    ctx.fillStyle = g
    ctx.beginPath()
    ctx.arc(p.x * dpr, p.y * dpr, r * 2.2, 0, Math.PI * 2)
    ctx.fill()
  }

  if (alive > 0) {
    raf = requestAnimationFrame(tick)
  } else {
    ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  }
}

const resize = () => {
  const c = canvasRef.value
  if (!c || !c.clientWidth) return
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  c.width = Math.round(c.clientWidth * dpr)
  c.height = Math.round(c.clientHeight * dpr)
}

onMounted(() => {
  ctx = canvasRef.value.getContext('2d')
  resize()
  ro = new ResizeObserver(resize)
  ro.observe(canvasRef.value)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  if (ro) ro.disconnect()
})

defineExpose({ splash })
</script>

<style scoped>
.splash-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 20;
}
</style>
