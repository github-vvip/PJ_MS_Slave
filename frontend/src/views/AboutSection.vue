<template>
  <section class="about-section">
    <div class="about-bg" :style="bgStyle"></div>
    <div class="about-overlay"></div>

    <div class="about-content">
      <div class="about-header">
        <div class="about-header-line"></div>
        <h2 class="about-title">客 户 A P K</h2>
        <p class="about-subtitle">CUSTOMER APK</p>
        <div class="about-header-line"></div>
      </div>

      <div class="about-body">
        <div class="about-text-col">
          <div class="about-card">
            <div class="about-card-border"></div>
            <div class="about-card-inner">
              <p class="about-paragraph">
                WhaleFramely_v2.2.x日历
              </p>
              <p class="about-paragraph about-paragraph-tight">
                链接：<a href="https://pan.baidu.com/s/1Gyepg3oMWJZ0PKvqAh27Mg?pwd=s6th" target="_blank" rel="noopener" style="color: #C9A96E; text-decoration: underline;">https://pan.baidu.com/s/1Gyepg3oMWJZ0PKvqAh27Mg?pwd=s6th</a>
              </p>
              <p class="about-paragraph">
                WhalePhoto_v2.1.x相框
              </p>
              <p class="about-paragraph about-paragraph-tight">
                链接：<a href="https://pan.baidu.com/s/1L5yVsIbJcpnaXg09SgEAPw?pwd=88kn" target="_blank" rel="noopener" style="color: #C9A96E; text-decoration: underline;">https://pan.baidu.com/s/1L5yVsIbJcpnaXg09SgEAPw?pwd=88kn</a>
              </p>
              <p class="about-paragraph">
                Uhale_v5.1.x相框
              </p>
              <p class="about-paragraph about-paragraph-tight">
                链接：<a href="https://pan.baidu.com/s/1i866rgS_JdjVErPaEcuh6w?pwd=8jh6" target="_blank" rel="noopener" style="color: #C9A96E; text-decoration: underline;">https://pan.baidu.com/s/1i866rgS_JdjVErPaEcuh6w?pwd=8jh6</a>
              </p>
            </div>
          </div>
        </div>

        <div class="about-image-col">
          <div class="about-image-frame">
            <div class="about-image-offset-border"></div>
            <div class="about-image-wrapper">
              <img :src="aboutImage" alt="Ballet" class="about-image" />
              <div class="about-image-overlay"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>

const cacheBust = `?t=${Date.now()}`

const bgStyle = {
  backgroundImage: `url('/DBbackup/Photo/BeiJing.png${cacheBust}')`
}

const aboutImage = `/DBbackup/Photo/BeiJing.png${cacheBust}`
</script>

<style scoped>
.about-section {
  position: relative;
  min-height: 600px;
  padding: 80px 24px 120px;
  overflow: hidden;
}

.about-bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  z-index: 0;
}

.about-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1;
}

.about-content {
  position: relative;
  z-index: 2;
  max-width: 1100px;
  margin: 0 auto;
}

.about-header {
  text-align: center;
  margin-bottom: 60px;
}

.about-header-line {
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #c9a96e, transparent);
  margin: 0 auto 20px;
}

.about-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 2.25rem;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 0.2em;
  margin: 0 0 8px;
}

.about-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  font-weight: 300;
  color: #c9a96e;
  letter-spacing: 0.3em;
  margin: 0 0 20px;
  text-transform: uppercase;
}

.about-body {
  display: flex;
  gap: 60px;
  align-items: stretch;
  margin-bottom: 60px;
}

.about-text-col {
  flex: 1;
  display: flex;
  align-items: center;
}

.about-card {
  position: relative;
  width: 100%;
}

.about-card-border {
  position: absolute;
  top: -16px;
  right: -16px;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(201, 169, 110, 0.1);
  border-radius: 4px;
  pointer-events: none;
}

.about-card-inner {
  background: rgba(13, 13, 13, 0.7);
  border: 1px solid rgba(201, 169, 110, 0.1);
  border-radius: 4px;
  padding: 40px 36px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.about-paragraph {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 15px;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  letter-spacing: 0.05em;
}

.about-paragraph + .about-paragraph {
  margin-top: 20px;
}

.about-paragraph-tight {
  margin-top: 8px !important;
}

.about-image-col {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.about-image-frame {
  position: relative;
  width: 100%;
  max-width: 460px;
}

.about-image-offset-border {
  position: absolute;
  top: -16px;
  right: -16px;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(201, 169, 110, 0.15);
  border-radius: 4px;
  pointer-events: none;
}

.about-image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border-radius: 4px;
  border: 1px solid rgba(201, 169, 110, 0.1);
}

.about-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.about-image-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 40%, rgba(13, 13, 13, 0.5) 100%);
  pointer-events: none;
}

.about-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 40px 0 0;
  border-top: 1px solid rgba(201, 169, 110, 0.1);
}

.about-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 0 24px;
}

.about-stat-value {
  font-family: 'Noto Serif SC', serif;
  font-size: 1.75rem;
  font-weight: 600;
  color: #c9a96e;
  letter-spacing: 0.05em;
}

.about-stat-label {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.1em;
}

.about-stat-divider {
  width: 1px;
  height: 48px;
  background: rgba(201, 169, 110, 0.15);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .about-section {
    padding: 60px 16px 80px;
  }

  .about-body {
    flex-direction: column;
    gap: 40px;
  }

  .about-title {
    font-size: 1.75rem;
  }

  .about-stats {
    flex-wrap: wrap;
    gap: 16px;
  }

  .about-stat {
    padding: 0 16px;
  }

  .about-stat-divider:nth-child(even) {
    display: none;
  }
}
</style>
