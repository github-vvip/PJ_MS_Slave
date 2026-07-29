<template>
  <canvas ref="canvasRef" class="water-canvas" aria-hidden="true"></canvas>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { WaterRenderer } from '../../composables/useWaterRenderer.js'

const emit = defineEmits(['unsupported'])

const canvasRef = ref(null)
let renderer = null
let ro = null

onMounted(() => {
  renderer = new WaterRenderer(canvasRef.value)
  renderer.onContextLost = () => emit('unsupported')
  const ok = renderer.init()
  if (!ok) {
    emit('unsupported')
    return
  }
  renderer.start()
  ro = new ResizeObserver(() => renderer && renderer.resize())
  ro.observe(canvasRef.value)
})

const addDrop = (x, y, radius = 5, strength = 0.6) => renderer && renderer.addDrop(x, y, radius, strength)
const pause = () => renderer && renderer.stop()
const resume = () => renderer && renderer.start()
const resize = () => renderer && renderer.resize()

defineExpose({ addDrop, pause, resume, resize })

onBeforeUnmount(() => {
  if (ro) ro.disconnect()
  if (renderer) renderer.destroy()
  renderer = null
})
</script>

<style scoped>
.water-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  z-index: 1;
}
</style>
