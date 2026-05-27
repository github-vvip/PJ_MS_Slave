<template>
  <section class="cast-section">
    <div class="cast-inner">
      <div class="cast-header">
        <div class="cast-header-line"></div>
        <h2 class="cast-title">演 员 介 绍</h2>
        <p class="cast-subtitle">THE CAST</p>
        <div class="cast-header-line"></div>
      </div>

      <div
        class="cast-carousel"
        @mouseenter="paused = true"
        @mouseleave="paused = false"
      >
        <div class="cast-track" :class="{ paused }">
          <div
            v-for="(member, idx) in duplicatedFeatured"
            :key="idx"
            class="cast-card"
          >
            <div class="cast-card-img-wrap">
              <img :src="member.image" :alt="member.name" class="cast-card-img" />
              <div class="cast-card-mask"></div>
            </div>
            <div class="cast-card-info">
              <span class="cast-card-name">{{ member.name }}</span>
              <span class="cast-card-role">{{ member.role }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const paused = ref(false)

const featured = [
  {
    name: '林 晓 雯',
    role: '首席舞者',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=female%20ballet%20dancer%20portrait%20professional%20headshot%20dark%20background%20elegant%20pose%20dramatic%20lighting&image_size=portrait_4_3'
  },
  {
    name: '赵 明 轩',
    role: '首席舞者',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=male%20ballet%20dancer%20portrait%20professional%20headshot%20dark%20background%20strong%20pose%20dramatic%20lighting&image_size=portrait_4_3'
  },
  {
    name: '苏 雨 晴',
    role: '独舞演员',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=female%20ballet%20dancer%20portrait%20graceful%20dark%20background%20soft%20lighting%20elegant&image_size=portrait_4_3'
  },
  {
    name: '陈 逸 飞',
    role: '独舞演员',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=male%20ballet%20dancer%20portrait%20confident%20dark%20background%20dramatic%20lighting%20strong&image_size=portrait_4_3'
  },
  {
    name: '周 瑶',
    role: '群舞领舞',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=female%20ballet%20dancer%20portrait%20delicate%20dark%20background%20warm%20lighting%20beautiful&image_size=portrait_4_3'
  },
  {
    name: '张 子 豪',
    role: '群舞领舞',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=male%20ballet%20dancer%20portrait%20powerful%20dark%20background%20spotlight%20intense&image_size=portrait_4_3'
  }
]

const duplicatedFeatured = computed(() => [...featured, ...featured])
</script>

<style scoped>
.cast-section {
  background: #E8EBED;
  padding: 80px 24px 120px;
  overflow: hidden;
}

.cast-inner {
  max-width: 1100px;
  margin: 0 auto;
}

.cast-header {
  text-align: center;
  margin-bottom: 48px;
}

.cast-header-line {
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #c9a96e, transparent);
  margin: 0 auto 20px;
}

.cast-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 2.25rem;
  font-weight: 600;
  color: #2D3748;
  letter-spacing: 0.2em;
  margin: 0 0 8px;
}

.cast-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  font-weight: 300;
  color: #718096;
  letter-spacing: 0.3em;
  margin: 0 0 20px;
  text-transform: uppercase;
}

.cast-carousel {
  width: 100vw;
  margin-left: calc(-50vw + 50%);
  overflow: hidden;
  position: relative;
}

.cast-carousel::before,
.cast-carousel::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 80px;
  z-index: 2;
  pointer-events: none;
}

.cast-carousel::before {
  left: 0;
  background: linear-gradient(to right, #E8EBED, transparent);
}

.cast-carousel::after {
  right: 0;
  background: linear-gradient(to left, #E8EBED, transparent);
}

.cast-track {
  display: flex;
  gap: 20px;
  width: max-content;
  animation: scrollLeft 30s linear infinite;
}

.cast-track.paused {
  animation-play-state: paused;
}

@keyframes scrollLeft {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

.cast-card {
  flex-shrink: 0;
  width: 180px;
  cursor: pointer;
  border: 1px solid transparent;
  border-radius: 4px;
  overflow: hidden;
  transition: border-color 0.3s ease, transform 0.4s ease;
}

.cast-carousel:hover .cast-card:hover {
  border-color: rgba(45, 55, 72, 0.2);
  transform: scale(1.05);
}

.cast-card-img-wrap {
  position: relative;
  aspect-ratio: 3 / 4;
  overflow: hidden;
}

.cast-card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.5s ease;
}

.cast-card:hover .cast-card-img {
  transform: scale(1.08);
}

.cast-card-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.6) 0%,
    transparent 30%,
    transparent 50%,
    rgba(0, 0, 0, 0.85) 100%
  );
  pointer-events: none;
}

.cast-card-info {
  padding: 12px 8px 0;
  text-align: center;
}

.cast-card-name {
  display: block;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: rgba(45, 55, 72, 0.8);
  letter-spacing: 0.15em;
  margin-bottom: 4px;
}

.cast-card-role {
  display: block;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 11px;
  color: rgba(45, 55, 72, 0.5);
  letter-spacing: 0.08em;
}

@media (max-width: 768px) {
  .cast-section {
    padding: 60px 16px 80px;
  }

  .cast-title {
    font-size: 1.75rem;
  }

  .cast-card {
    width: 140px;
  }

  .cast-track {
    gap: 12px;
    animation-duration: 22s;
  }
}
</style>
