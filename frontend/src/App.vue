<template>
  <router-view />
</template>

<script setup>
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;600&display=swap');

html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #1E293B;
  background: #F8FAFC;
}

* {
  box-sizing: border-box;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94A3B8;
}

.el-dialog {
  border-radius: 12px !important;
}
.el-dialog__header {
  border-bottom: 1px solid #F1F5F9;
  padding-bottom: 16px !important;
}
.el-dialog__title {
  font-weight: 600 !important;
  font-size: 16px !important;
  color: #0F172A !important;
}
.el-button--primary {
  --el-button-bg-color: #2563EB;
  --el-button-border-color: #2563EB;
  --el-button-hover-bg-color: #1D4ED8;
  --el-button-hover-border-color: #1D4ED8;
}
.el-checkbox__input.is-checked .el-checkbox__inner {
  background-color: #2563EB;
  border-color: #2563EB;
}
.el-tag--success {
  --el-tag-bg-color: #ECFDF5;
  --el-tag-border-color: #A7F3D0;
  --el-tag-text-color: #065F46;
}
.el-tag--info {
  --el-tag-bg-color: #F1F5F9;
  --el-tag-border-color: #E2E8F0;
  --el-tag-text-color: #64748B;
}
.el-input__wrapper {
  border-radius: 8px !important;
}
.el-select .el-input__wrapper {
  border-radius: 8px !important;
}
.el-pagination.is-background .el-pager li.is-active {
  background-color: #2563EB !important;
}
</style>
