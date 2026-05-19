import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const ripple = {
  mounted(el) {
    el.style.position = 'relative'
    el.style.overflow = 'hidden'
    el.addEventListener('click', (e) => {
      const rect = el.getBoundingClientRect()
      const size = Math.max(rect.width, rect.height) * 2
      const x = e.clientX - rect.left - size / 2
      const y = e.clientY - rect.top - size / 2
      const span = document.createElement('span')
      span.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255,255,255,0.35);
        border-radius: 50%;
        transform: scale(0);
        pointer-events: none;
        animation: ripple-effect 0.6s ease-out forwards;
      `
      el.appendChild(span)
      span.addEventListener('animationend', () => span.remove())
    })
  }
}

const style = document.createElement('style')
style.textContent = `
@keyframes ripple-effect {
  to {
    transform: scale(1);
    opacity: 0;
  }
}
`
document.head.appendChild(style)

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.directive('ripple', ripple)
app.use(ElementPlus, { locale: zhCn })
app.use(router)
app.mount('#app')
