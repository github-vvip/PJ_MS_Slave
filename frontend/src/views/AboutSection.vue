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
              <div v-for="item in apkLinks" :key="item.id" class="apk-item">
                <p class="about-paragraph apk-title-row" @dblclick="startEdit(item, 'title')">
                  <template v-if="isEditing(item.id, 'title')">
                    <input
                      :ref="el => { if (el) editInputEl = el }"
                      v-model="editValue"
                      class="apk-edit-input"
                      @keyup.enter="saveEdit(item)"
                      @keyup.escape="cancelEdit"
                      @blur="saveEdit(item)"
                    />
                  </template>
                  <template v-else>
                    {{ item.title }}
                    <span class="apk-hint">双击编辑</span>
                  </template>
                </p>
                <p class="about-paragraph about-paragraph-tight apk-link-row">
                  <span class="apk-link-label">链接：</span>
                  <template v-if="isEditing(item.id, 'url')">
                    <input
                      :ref="el => { if (el) editInputEl = el }"
                      v-model="editValue"
                      class="apk-edit-input apk-edit-input-url"
                      @keyup.enter="saveEdit(item)"
                      @keyup.escape="cancelEdit"
                      @blur="saveEdit(item)"
                    />
                  </template>
                  <template v-else>
                    <span class="apk-link-text" @dblclick.stop="startEdit(item, 'url')">{{ item.url }}</span>
                    <a :href="item.url" target="_blank" rel="noopener" class="apk-open-btn" title="在新标签页打开">↗</a>
                    <span class="apk-delete-btn" @click.stop="handleDelete(item)">✕</span>
                  </template>
                </p>
              </div>
              <div v-if="apkLinks.length === 0" class="apk-empty">暂无APK链接</div>
              <button class="apk-add-btn" @click="handleAdd">+ 新增APK</button>
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
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getApkLinks, createApkLink, updateApkLink, deleteApkLink } from '../api/api.js'

const cacheBust = `?t=${Date.now()}`

const bgStyle = {
  backgroundImage: `url('/DBbackup/Photo/BeiJing.png${cacheBust}')`
}

const aboutImage = `/DBbackup/Photo/BeiJing.png${cacheBust}`

// ===== APK 链接管理 =====
const apkLinks = ref([])
const editingId = ref(null)
const editField = ref(null)
const editValue = ref('')
const editInputEl = ref(null)

const isEditing = (id, field) => editingId.value === id && editField.value === field

const loadApkLinks = async () => {
  try {
    apkLinks.value = await getApkLinks()
  } catch (e) {
    ElMessage.error('加载APK链接失败')
  }
}

const startEdit = (item, field) => {
  editingId.value = item.id
  editField.value = field
  editValue.value = item[field]
  nextTick(() => {
    editInputEl.value?.focus()
    editInputEl.value?.select()
  })
}

const saveEdit = async (item) => {
  if (editingId.value === null) return
  const field = editField.value
  const newValue = editValue.value.trim()
  // 先清空编辑状态，避免 async 期间与新编辑冲突
  editingId.value = null
  editField.value = null
  if (!newValue || newValue === item[field]) return
  try {
    await updateApkLink(item.id, { [field]: newValue })
    item[field] = newValue
    ElMessage.success('已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const cancelEdit = () => {
  editingId.value = null
  editField.value = null
}

const handleAdd = async () => {
  try {
    const maxOrder = apkLinks.value.length > 0
      ? Math.max(...apkLinks.value.map(a => a.order))
      : 0
    const res = await createApkLink({
      title: '新APK',
      url: 'https://',
      order: maxOrder + 1
    })
    apkLinks.value.push(res)
    startEdit(res, 'title')
  } catch (e) {
    ElMessage.error('新增失败')
  }
}

const handleDelete = async (item) => {
  try {
    await ElMessageBox.confirm(`确定删除"${item.title}"？`, '删除确认', { type: 'warning' })
    await deleteApkLink(item.id)
    apkLinks.value = apkLinks.value.filter(a => a.id !== item.id)
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadApkLinks()
})
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

/* ===== APK 内联编辑样式 ===== */
.apk-item {
  position: relative;
  padding: 4px 0;
}
.apk-item + .apk-item {
  border-top: 1px solid rgba(201, 169, 110, 0.08);
  margin-top: 16px;
  padding-top: 16px;
}
.apk-title-row {
  cursor: default;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.apk-link-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.apk-link-label {
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}
.apk-link-text {
  color: #C9A96E;
  text-decoration: underline;
  word-break: break-all;
  cursor: default;
}
.apk-open-btn {
  margin-left: 6px;
  color: rgba(201, 169, 110, 0.5);
  text-decoration: none;
  font-size: 13px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s, color 0.2s;
}
.apk-open-btn:hover {
  color: #C9A96E;
}
.apk-hint {
  font-size: 11px;
  color: rgba(201, 169, 110, 0.3);
  opacity: 0;
  transition: opacity 0.2s;
  font-weight: 300;
}
.apk-title-row:hover .apk-hint {
  opacity: 1;
}
.apk-delete-btn {
  margin-left: 8px;
  color: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.2s, color 0.2s;
  flex-shrink: 0;
}
.apk-delete-btn:hover {
  color: #e95555;
}
.apk-link-row:hover .apk-open-btn,
.apk-link-row:hover .apk-delete-btn {
  opacity: 1;
}
.apk-edit-input {
  flex: 1;
  min-width: 0;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(201, 169, 110, 0.4);
  border-radius: 4px;
  padding: 4px 10px;
  color: #fff;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 15px;
  line-height: 1.5;
  outline: none;
  transition: border-color 0.2s;
}
.apk-edit-input:focus {
  border-color: #C9A96E;
}
.apk-edit-input-url {
  font-family: 'Courier New', monospace;
  font-size: 14px;
}
.apk-empty {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  text-align: center;
  padding: 20px 0;
}
.apk-add-btn {
  margin-top: 20px;
  padding: 6px 16px;
  border: 1px dashed rgba(201, 169, 110, 0.3);
  border-radius: 4px;
  background: transparent;
  color: rgba(201, 169, 110, 0.6);
  font-size: 13px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.25s ease, border-color 0.25s ease, color 0.25s ease, background 0.25s ease;
  font-family: 'Noto Sans SC', sans-serif;
}
.about-card:hover .apk-add-btn {
  opacity: 1;
}
.apk-add-btn:hover {
  border-color: #C9A96E;
  color: #C9A96E;
  background: rgba(201, 169, 110, 0.05);
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
