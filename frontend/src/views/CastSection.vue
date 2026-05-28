<template>
  <section class="cast-section">
    <div class="cast-inner">
      <div class="cast-header">
        <div class="cast-header-line"></div>
        <h2 class="cast-title">科 技 前 沿</h2>
        <p class="cast-subtitle">TECH FRONTIERS</p>
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
    name: 'AI 芯片',
    role: '半导体创新',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=AI%20microchip%20close-up%20glowing%20neural%20network%20circuit%20blue%20and%20gold%20traces%20dark%20background%20futuristic%20semiconductor%20technology%20highly%20detailed&image_size=portrait_4_3'
  },
  {
    name: '量子计算',
    role: '计算革命',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=quantum%20computer%20processor%20dilution%20refrigerator%20golden%20chandelier%20cables%20dark%20lab%20blue%20glow%20cutting%20edge%20technology%20cinematic&image_size=portrait_4_3'
  },
  {
    name: '智能机器人',
    role: '智造未来',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=humanoid%20robot%20sleek%20white%20metallic%20body%20glowing%20blue%20eyes%20dark%20studio%20background%20advanced%20AI%20robotics%20dramatic%20lighting&image_size=portrait_4_3'
  },
  {
    name: '5G 通信',
    role: '万物互联',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=5G%20communication%20tower%20emitting%20holographic%20network%20waves%20connected%20devices%20smart%20city%20skyline%20dark%20blue%20background%20digital%20mesh%20futuristic&image_size=portrait_4_3'
  },
  {
    name: '增强现实',
    role: '虚实融合',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=augmented%20reality%20headset%20holographic%20UI%20floating%20data%20visualizations%20hand%20gesture%20interaction%20dark%20environment%20cyan%20glow%20future%20tech&image_size=portrait_4_3'
  },
  {
    name: '新能源科技',
    role: '绿色未来',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=futuristic%20solid%20state%20battery%20glowing%20green%20energy%20core%20solar%20panel%20elements%20clean%20energy%20technology%20dark%20background%20emerald%20light%20innovation&image_size=portrait_4_3'
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
