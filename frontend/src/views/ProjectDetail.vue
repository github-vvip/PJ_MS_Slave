<template>
  <el-drawer :model-value="visible" title="项目详情" size="480px" @close="handleClose">
    <el-descriptions v-if="detailData" :column="1" border>
      <el-descriptions-item label="序号">{{ detailData.serial_number }}</el-descriptions-item>
      <el-descriptions-item label="项目名称">{{ detailData.project_name }}</el-descriptions-item>
      <el-descriptions-item label="硬件版型">{{ detailData.hardware_version || '-' }}</el-descriptions-item>
      <el-descriptions-item label="Android版本">{{ detailData.android_version || '-' }}</el-descriptions-item>
      <el-descriptions-item label="厂商">{{ detailData.brand || '-' }}</el-descriptions-item>
      <el-descriptions-item label="型号">{{ detailData.model || '-' }}</el-descriptions-item>
      <el-descriptions-item label="Launcher">{{ detailData.launcher || '-' }}</el-descriptions-item>
      <el-descriptions-item label="PIR">
        <el-tag :type="detailData.pir ? 'success' : 'info'" size="small" effect="plain">{{ detailData.pir ? '有' : '无' }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="LED">
        <el-tag :type="detailData.led ? 'success' : 'info'" size="small" effect="plain">{{ detailData.led ? '有' : '无' }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="光感">{{ detailData.light_sensor }}</el-descriptions-item>
      <el-descriptions-item label="WiFi">{{ detailData.wifi }}</el-descriptions-item>
      <el-descriptions-item label="屏幕尺寸">{{ detailData.screen_size || '-' }}</el-descriptions-item>
      <el-descriptions-item label="屏幕型号">{{ detailData.screen_model || '-' }}</el-descriptions-item>
      <el-descriptions-item label="TP">{{ detailData.tp || '-' }}</el-descriptions-item>
      <el-descriptions-item label="壳">{{ detailData.shell || '-' }}</el-descriptions-item>
      <el-descriptions-item label="立项时间">{{ detailData.project_establish_date || '-' }}</el-descriptions-item>
      <el-descriptions-item label="备注">{{ detailData.remarks || '-' }}</el-descriptions-item>
    </el-descriptions>
  </el-drawer>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, required: true },
  detailData: { type: Object, default: null }
})

const emit = defineEmits(['close'])

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
</style>
