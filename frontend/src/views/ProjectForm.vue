<template>
  <el-dialog :model-value="visible" :title="isEdit ? '编辑项目' : '新增项目'" width="750px" @close="handleClose">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" class="project-form">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="所属客户">
            <el-input :model-value="customerName" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="项目名称" prop="project_name">
            <el-input v-model="form.project_name" placeholder="请输入项目名称" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="硬件版型">
            <el-input v-model="form.hardware_version" placeholder="请输入硬件版型" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Android版本">
            <el-input v-model="form.android_version" placeholder="请输入Android版本" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="厂商">
            <el-input v-model="form.brand" placeholder="请输入厂商" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="型号">
            <el-input v-model="form.model" placeholder="请输入型号" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="Launcher">
            <el-input v-model="form.launcher" placeholder="请输入Launcher" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="PIR">
            <el-switch v-model="form.pir" active-text="有" inactive-text="无" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="LED">
            <el-switch v-model="form.led" active-text="有" inactive-text="无" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="光感">
            <el-select v-model="form.light_sensor" style="width: 100%;">
              <el-option label="ADCF3" value="ADCF3" />
              <el-option label="STK3311" value="STK3311" />
              <el-option label="无" value="无" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="WiFi">
            <el-select v-model="form.wifi" style="width: 100%;">
              <el-option label="2.4G" value="2.4G" />
              <el-option label="5G" value="5G" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="立项时间">
            <el-date-picker
              v-model="form.project_establish_date"
              type="date"
              placeholder="请选择立项时间"
              value-format="YYYY-MM-DD"
              style="width: 100%;"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="屏幕尺寸">
            <el-input v-model="form.screen_size" placeholder="请输入屏幕尺寸" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="屏幕型号">
            <el-input v-model="form.screen_model" placeholder="请输入屏幕型号" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="TP">
            <el-input v-model="form.tp" placeholder="请输入TP" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="壳">
            <el-input v-model="form.shell" placeholder="请输入壳" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="24">
          <el-form-item label="备注">
            <el-input v-model="form.remarks" type="textarea" :rows="3" placeholder="请输入备注" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createProject, updateProject, getCustomers } from '../api/api.js'

const props = defineProps({
  visible: { type: Boolean, required: true },
  editData: { type: Object, default: null },
  customerId: { type: Number, default: null }
})

const emit = defineEmits(['close', 'saved'])

const formRef = ref(null)
const submitting = ref(false)
const customerName = ref('')

const isEdit = computed(() => !!props.editData)

const defaultForm = () => ({
  customer: props.customerId,
  project_name: '',
  hardware_version: '',
  android_version: '',
  brand: '',
  model: '',
  launcher: '',
  pir: false,
  led: false,
  light_sensor: '无',
  wifi: '2.4G',
  screen_size: '',
  screen_model: '',
  tp: '',
  shell: '',
  project_establish_date: '',
  remarks: ''
})

const form = ref(defaultForm())

const rules = {
  project_name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' }
  ]
}

const loadCustomerName = async () => {
  if (!props.customerId) return
  try {
    const list = await getCustomers()
    const c = list.find(c => c.id === props.customerId)
    customerName.value = c ? c.name : ''
  } catch (e) { /* 忽略 */ }
}

watch(() => props.visible, (val) => {
  if (val) {
    if (props.editData) {
      form.value = { ...defaultForm(), ...props.editData }
      customerName.value = props.editData.customer_name || ''
    } else {
      form.value = defaultForm()
      loadCustomerName()
    }
  }
}, { immediate: true })

const handleClose = () => {
  emit('close')
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch { return }

  submitting.value = true
  try {
    const data = { ...form.value }
    if (!data.customer) data.customer = props.customerId
    if (isEdit.value) {
      await updateProject(props.editData.id, data)
      ElMessage.success('修改成功')
    } else {
      await createProject(data)
      ElMessage.success('新增成功')
    }
    emit('saved')
  } catch (e) {
    ElMessage.error(isEdit.value ? '修改失败' : '新增失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.project-form {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 10px;
}
</style>
