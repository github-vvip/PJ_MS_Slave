<template>
  <div class="project-page">
    <div class="page-header">
      <h1 class="page-title">项目配置表</h1>
    </div>

    <div class="filter-card">
      <div class="search-bar">
        <div class="search-input-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchText"
            type="text"
            placeholder="搜索项目名称 / 厂商 / 型号"
            class="search-input"
            @keyup.enter="loadProjects"
          />
          <span v-if="searchText" class="search-clear" @click="clearSearch">×</span>
        </div>
        <button class="search-btn" v-ripple :class="{ 'is-loading': searchLoading }" @click="loadProjects">
          <span v-if="searchLoading" class="btn-spinner"></span>
          <span v-else>搜索</span>
        </button>
      </div>
      <div class="filter-row">
        <el-select v-model="filterHardware" placeholder="硬件版型" clearable multiple collapse-tags class="filter-select" size="small" @change="loadProjects">
          <el-option v-for="v in uniqueHardwareVersions" :key="v" :label="v" :value="v" />
        </el-select>
        <el-select v-model="filterAndroid" placeholder="Android版本" clearable multiple collapse-tags class="filter-select" size="small" @change="loadProjects">
          <el-option v-for="v in uniqueAndroidVersions" :key="v" :label="v" :value="v" />
        </el-select>
        <el-select v-model="filterScreenSize" placeholder="屏幕尺寸" clearable multiple collapse-tags class="filter-select filter-select-multi" size="small" @change="loadProjects">
          <el-option v-for="v in uniqueScreenSizes" :key="v" :label="v" :value="v" />
        </el-select>
        <el-select v-model="filterTP" placeholder="TP" clearable multiple collapse-tags class="filter-select filter-select-multi" size="small" @change="loadProjects">
          <el-option v-for="v in uniqueTPs" :key="v" :label="v" :value="v" />
        </el-select>
        <button class="reset-btn" v-ripple @click="resetFilters">
          <el-icon class="reset-icon"><RefreshLeft /></el-icon>
          <span>重置</span>
        </button>
      </div>
    </div>

    <div class="customer-cards-wrapper">
      <div class="customer-cards" ref="tabsRef" @wheel.prevent="onTabsWheel">
        <div
          v-for="(c, idx) in customers"
          :key="c.id"
          class="customer-card scroll-reveal"
          :class="{ active: currentCustomerId === c.id }"
          :style="{ '--reveal-delay': idx * 60 + 'ms' }"
          @click="selectCustomer(c.id)"
          @contextmenu.prevent="showContextMenu($event, c)"
        >
          <div class="card-icon" :style="{ background: cardColors[idx % cardColors.length] }">
            <span v-if="editingCustomerId !== c.id">{{ c.name.charAt(0) }}</span>
            <input
              v-else
              class="card-edit-input"
              v-model="editingCustomerName"
              @blur="confirmEditCustomer"
              @keyup.enter="confirmEditCustomer"
              @keyup.escape="cancelEditCustomer"
              ref="editInputRef"
            />
          </div>
          <div class="card-info">
            <span class="card-label" v-if="editingCustomerId !== c.id">{{ c.name }}</span>
            <span class="card-number">{{ c.project_count }}</span>
          </div>
        </div>
        <div class="customer-card card-add scroll-reveal" :style="{ '--reveal-delay': customers.length * 60 + 'ms' }" @click="handleAddCustomer">
          <div class="card-icon card-icon-add">
            <el-icon :size="20"><Plus /></el-icon>
          </div>
          <div class="card-info">
            <span class="card-number">+</span>
            <span class="card-label">新增客户</span>
          </div>
        </div>
      </div>
    </div>

    <Transition name="fade-slide" mode="out-in">
      <div class="table-section" :key="currentCustomerId || 'all'">
        <div class="table-toolbar">
          <span class="table-customer-label">{{ currentCustomerName || '全部项目' }}</span>
          <div class="table-actions">
            <el-button v-if="currentCustomerId" type="primary" :icon="Plus" size="small" v-ripple @click="handleAddProject">新建项目</el-button>
            <el-button v-if="currentCustomerId" :icon="Upload" size="small" v-ripple @click="handleImportClick">导入 Excel</el-button>
            <el-button :icon="Download" size="small" v-ripple @click="handleExport">导出 Excel</el-button>
            <el-button :icon="Setting" size="small" v-ripple @click="showColumnSettings = true">展示设置</el-button>
          </div>
        </div>

        <div class="table-card scroll-reveal">
          <el-table
          :data="pagedData"
          border
          style="width: 100%"
          row-key="id"
          @row-dblclick="handleViewDetail"
          :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: 600, fontSize: '13px' }"
          :cell-style="{ fontSize: '13px', color: '#334155' }"
        >
          <el-table-column v-if="visibleColumns.serial_number" prop="serial_number" label="序号" width="70" align="center" />
          <el-table-column v-if="!currentCustomerId && visibleColumns.customer_name" prop="customer_name" label="客户" width="100" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.project_name" prop="project_name" label="项目名称" min-width="120" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.hardware_version" prop="hardware_version" label="硬件版型" width="110" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.brand" prop="brand" label="厂商" width="90" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.model" prop="model" label="型号" width="90" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.android_version" prop="android_version" label="Android版本" width="110" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.launcher" prop="launcher" label="Launcher" width="100" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.pir" prop="pir" label="PIR" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.pir ? 'success' : 'info'" size="small" effect="plain">{{ row.pir ? '有' : '无' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="visibleColumns.led" prop="led" label="LED" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.led ? 'success' : 'info'" size="small" effect="plain">{{ row.led ? '有' : '无' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="visibleColumns.light_sensor" prop="light_sensor" label="光感" width="80" align="center" />
          <el-table-column v-if="visibleColumns.wifi" prop="wifi" label="WiFi" width="80" align="center" />
          <el-table-column v-if="visibleColumns.screen_size" prop="screen_size" label="屏幕尺寸" width="100" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.screen_model" prop="screen_model" label="屏幕型号" width="120" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.tp" prop="tp" label="TP" width="100" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.shell" prop="shell" label="壳" width="100" align="center" show-overflow-tooltip />
          <el-table-column v-if="visibleColumns.project_establish_date" prop="project_establish_date" label="立项时间" width="110" align="center">
            <template #default="{ row }">{{ row.project_establish_date || '-' }}</template>
          </el-table-column>
          <el-table-column v-if="visibleColumns.remarks" prop="remarks" label="备注" min-width="120" align="center" show-overflow-tooltip />
          <el-table-column label="操作" width="150" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleViewDetail(row)">详情</el-button>
              <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-area">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 15, 20, 50]"
            :total="projectList.length"
            layout="total, sizes, prev, pager, next, jumper"
            background
            small
          />
        </div>
      </div>
    </div>
    </Transition>

    <ProjectForm
      v-if="showForm"
      :visible="showForm"
      :edit-data="editData"
      :customer-id="currentCustomerId"
      @close="showForm = false"
      @saved="onFormSaved"
    />

    <ProjectDetail
      v-if="showDetail"
      :visible="showDetail"
      :detail-data="detailData"
      @close="showDetail = false"
    />

    <el-dialog v-model="showAddCustomerDialog" title="新增客户" width="400px" @close="newCustomerName = ''">
      <el-form @submit.prevent="confirmAddCustomer">
        <el-form-item label="客户名称">
          <el-input v-model="newCustomerName" placeholder="请输入客户名称" @keyup.enter="confirmAddCustomer" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCustomerDialog = false">取消</el-button>
        <el-button type="primary" :loading="addCustomerLoading" @click="confirmAddCustomer">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showColumnSettings" title="展示设置" width="480px">
      <div class="column-settings-body">
        <div class="column-settings-tip">点击字段可切换显示/隐藏</div>
        <div class="column-settings-grid">
          <div
            v-for="col in allColumns"
            :key="col.key"
            class="column-chip"
            :class="{ active: visibleColumns[col.key] }"
            @click="toggleColumn(col.key)"
          >
            <el-icon v-if="visibleColumns[col.key]" class="chip-check"><Check /></el-icon>
            <span>{{ col.label }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="resetColumnSettings">恢复默认</el-button>
        <el-button type="primary" @click="showColumnSettings = false">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showImportDialog" title="导入 Excel" width="600px" @close="resetImportState">
      <div class="import-body">
        <div v-if="importStep === 1" class="import-step">
          <el-upload
            ref="importUploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleImportFileChange"
            :on-exceed="() => ElMessage.warning('只能上传一个文件')"
            class="import-upload"
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">将 Excel 文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">仅支持 .xlsx / .xls 格式</div>
              <div class="el-upload__tip">表头需要在3行内，1 / 2 / 3任意一行都可以自动识别</div>
            </template>
          </el-upload>
        </div>

        <div v-if="importStep === 2" class="import-step">
          <div class="import-preview-info">
            <span>共解析到 <strong>{{ importParsedData.length }}</strong> 条数据</span>
            <span v-if="importUnmatchedHeaders.length > 0" class="import-unmatched">
              未识别列：{{ importUnmatchedHeaders.join('、') }}
            </span>
          </div>
          <div class="import-preview-table-wrapper">
            <el-table :data="importParsedData.slice(0, 10)" border size="small" max-height="320">
              <el-table-column
                v-for="col in importPreviewColumns"
                :key="col.key"
                :prop="col.key"
                :label="col.label"
                min-width="100"
                show-overflow-tooltip
                :class-name="col.unmatched ? 'unmatched-col' : ''"
                :header-cell-class-name="col.unmatched ? 'unmatched-header' : ''"
              >
                <template #header v-if="col.unmatched">
                  <span class="unmatched-label">{{ col.label }}</span>
                  <el-tag size="small" type="info" effect="plain" class="unmatched-tag">未识别</el-tag>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="importParsedData.length > 10" class="import-preview-more">仅预览前 10 条，共 {{ importParsedData.length }} 条</div>
          </div>
        </div>

        <div v-if="importStep === 3" class="import-step">
          <div class="import-result">
            <el-result :icon="importResult.errors.length > 0 ? 'warning' : 'success'" :title="importResultTitle">
              <template #sub-title>
                <div class="import-result-detail">
                  <p>新增：<strong>{{ importResult.created }}</strong> 条</p>
                  <p>更新：<strong>{{ importResult.updated }}</strong> 条</p>
                  <p>跳过：<strong>{{ importResult.skipped }}</strong> 条</p>
                  <div v-if="importResult.errors.length > 0" class="import-result-errors">
                    <p>详细信息：</p>
                    <ul>
                      <li v-for="(err, i) in importResult.errors" :key="i">{{ err }}</li>
                    </ul>
                  </div>
                </div>
              </template>
            </el-result>
          </div>
        </div>
      </div>
      <template #footer>
        <template v-if="importStep === 1">
          <el-button @click="showImportDialog = false">取消</el-button>
          <el-button type="primary" :disabled="!importFile" @click="parseImportFile">下一步</el-button>
        </template>
        <template v-if="importStep === 2">
          <el-button @click="importStep = 1">上一步</el-button>
          <el-button type="primary" :loading="importLoading" @click="executeImport">确认导入</el-button>
        </template>
        <template v-if="importStep === 3">
          <el-button type="primary" @click="showImportDialog = false">完成</el-button>
        </template>
      </template>
    </el-dialog>

    <div v-if="contextMenuVisible" class="context-menu" :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }">
      <div class="context-menu-item" @click="handleEditCustomerFromMenu">重命名</div>
      <div class="context-menu-item danger" @click="handleDeleteCustomer">删除</div>
    </div>

    <section class="concert-section">
      <div class="concert-header">
        <h2 class="concert-title">配 置 雷 达</h2>
        <p class="concert-subtitle">CONFIGURATION RADAR</p>
      </div>

      <!-- 检索按钮 -->
      <div class="concert-search-bar">
        <button class="concert-search-btn" :class="{ 'is-loading': radarLoading }" @click="handleRadarSearch" :disabled="radarLoading">
          <el-icon v-if="!radarLoading" class="concert-search-icon" size="16"><Search /></el-icon>
          <span v-if="radarLoading" class="concert-spinner"></span>
          <span>{{ radarLoading ? '检索中...' : '检 索' }}</span>
        </button>
      </div>

      <!-- 结果表格 -->
      <div v-if="radarResults.length > 0" class="concert-results">
        <el-table :data="radarResults" border stripe style="width: 100%" max-height="600" @sort-change="handleRadarSort">
          <el-table-column prop="客户" label="客户" sortable="custom" width="120" show-overflow-tooltip />
          <el-table-column prop="厂商" label="厂商" sortable="custom" width="120" show-overflow-tooltip />
          <el-table-column prop="项目名称" label="项目名称" sortable="custom" min-width="200" show-overflow-tooltip />
          <el-table-column prop="硬件版型" label="硬件版型" sortable="custom" width="120" />
          <el-table-column prop="Android版本" label="Android版本" sortable="custom" width="130" />
          <el-table-column prop="Launcher" label="Launcher" sortable="custom" width="100" />
          <el-table-column prop="配置表路径" label="配置表路径" min-width="320" show-overflow-tooltip>
            <template #default="{ row }">
              <el-tooltip :content="row.配置表路径" placement="top">
                <el-link type="primary" :underline="false" style="cursor: pointer" @click="copyRadarPath(row.配置表路径)">
                  {{ row.配置表路径 }}
                </el-link>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
        <div class="concert-result-count">共 {{ radarResults.length }} 条记录</div>
      </div>

      <!-- 无结果提示 -->
      <div v-else-if="radarDone && !radarLoading" class="concert-empty">
        <el-empty description="未检索到匹配的项目配置" />
      </div>

      <!-- 错误提示 -->
      <div v-if="radarError" class="concert-error">
        <el-alert :title="radarError" type="error" show-icon :closable="false" />
      </div>
    </section>

    <section class="concert-section">
      <div class="concert-header">
        <h2 class="concert-title">数 据 同 步</h2>
        <p class="concert-subtitle">DATA SYNCHRONIZATION</p>
      </div>

      <!-- 同步区域：按钮 + 日志窗口 -->
      <div class="sync-layout">
        <!-- 左侧：一键同步按钮 -->
        <div class="sync-btn-wrapper">
          <button class="sync-btn" :class="{ 'is-loading': syncing }" @click="handleSync" :disabled="syncing">
            <span v-if="syncing" class="sync-spinner"></span>
            <el-icon v-else size="20"><Upload /></el-icon>
            <span>{{ syncing ? '同步中...' : '一键同步' }}</span>
          </button>
        </div>

        <!-- 右侧：日志窗口 -->
        <div class="sync-log-window" ref="logWindowRef">
          <div v-if="syncLogs.length === 0 && !syncing" class="sync-log-placeholder">
            点击「一键同步」开始同步数据
          </div>
          <div
            v-for="(log, idx) in syncLogs"
            :key="idx"
            class="sync-log-item"
            :class="'sync-log-' + log.status"
          >
            <span class="sync-log-icon">
              <template v-if="log.status === 'info'">🔵</template>
              <template v-else-if="log.status === 'success'">🟢</template>
              <template v-else-if="log.status === 'skipped'">🟡</template>
              <template v-else-if="log.status === 'failed'">🔴</template>
            </span>
            <span class="sync-log-text">{{ log.message }}</span>
          </div>

          <!-- 汇总报告 -->
          <div v-if="syncSummary" class="sync-summary">
            <div class="sync-summary-divider">━━━━━ 同步报告 ━━━━━</div>
            <div class="sync-summary-item">📊 共检索到：{{ syncSummary.totalProjects }} 个项目</div>
            <div class="sync-summary-item">📋 含需求表：{{ syncSummary.withRequirementTable }} 个项目</div>
            <div class="sync-summary-item">✅ 成功同步：{{ syncSummary.syncedSuccessfully }} 个
              <span v-if="syncSummary.syncedSuccessfullyDetails" class="sync-summary-sub">
                <span v-for="(count, customer) in syncSummary.syncedSuccessfullyDetails" :key="customer">
                  · {{ customer }}：{{ count }}
                </span>
              </span>
            </div>
            <div class="sync-summary-item">⏭️ 跳过同步：{{ syncSummary.skipped }} 个
              <span v-if="syncSummary.skipDetails" class="sync-summary-sub">
                <span v-for="(count, reason) in syncSummary.skipDetails" :key="reason">
                  · {{ reason }}：{{ count }}
                </span>
              </span>
            </div>
            <div class="sync-summary-item">❌ 导入失败：{{ syncSummary.failedToImport }} 个
              <span v-if="syncSummary.failDetails" class="sync-summary-sub">
                <span v-for="(count, reason) in syncSummary.failDetails" :key="reason">
                  · {{ reason }}：{{ count }}
                </span>
              </span>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="syncError" class="sync-error-bar">
            {{ syncError }}
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Upload, Search, Setting, Check, RefreshLeft } from '@element-plus/icons-vue'
import {
  getCustomers, createCustomer, updateCustomer, deleteCustomer,
  getProjects, deleteProject, getProjectFilterOptions, batchImportProjects,
  searchProjects, executeDataSync
} from '../api/api.js'
import ProjectForm from './ProjectForm.vue'
import ProjectDetail from './ProjectDetail.vue'
import * as XLSX from 'xlsx'

const STORAGE_KEY = 'project_column_settings'

const allColumns = [
  { key: 'serial_number', label: '序号' },
  { key: 'customer_name', label: '客户' },
  { key: 'project_name', label: '项目名称' },
  { key: 'hardware_version', label: '硬件版型' },
  { key: 'brand', label: '厂商' },
  { key: 'model', label: '型号' },
  { key: 'android_version', label: 'Android版本' },
  { key: 'launcher', label: 'Launcher' },
  { key: 'pir', label: 'PIR' },
  { key: 'led', label: 'LED' },
  { key: 'light_sensor', label: '光感' },
  { key: 'wifi', label: 'WiFi' },
  { key: 'screen_size', label: '屏幕尺寸' },
  { key: 'screen_model', label: '屏幕型号' },
  { key: 'tp', label: 'TP' },
  { key: 'shell', label: '壳' },
  { key: 'project_establish_date', label: '立项时间' },
  { key: 'remarks', label: '备注' },
]

const defaultVisible = {
  customer_name: true,
  serial_number: true,
  project_name: true,
  hardware_version: true,
  brand: false,
  model: false,
  android_version: true,
  launcher: true,
  pir: false,
  led: false,
  light_sensor: false,
  wifi: false,
  screen_size: true,
  screen_model: true,
  tp: true,
  shell: false,
  project_establish_date: true,
  remarks: false,
}

const loadColumnSettings = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return JSON.parse(saved)
  } catch (e) { /* 忽略 */ }
  return { ...defaultVisible }
}

const visibleColumns = reactive(loadColumnSettings())
const showColumnSettings = ref(false)

watch(visibleColumns, (val) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
}, { deep: true })

const toggleColumn = (key) => {
  visibleColumns[key] = !visibleColumns[key]
}

const resetColumnSettings = () => {
  Object.assign(visibleColumns, defaultVisible)
}

const customers = ref([])
const currentCustomerId = ref(null)
const projectList = ref([])
const filterOptions = ref({ hardware_versions: [], android_versions: [], brands: [], screen_sizes: [], tps: [] })
const searchText = ref('')
const filterHardware = ref([])
const filterAndroid = ref([])
const filterScreenSize = ref([])
const filterTP = ref([])
const currentPage = ref(1)
const pageSize = ref(15)
const showForm = ref(false)
const editData = ref(null)
const showDetail = ref(false)
const detailData = ref(null)

const showAddCustomerDialog = ref(false)
const newCustomerName = ref('')
const editingCustomerId = ref(null)
const editingCustomerName = ref('')
const editInputRef = ref(null)
const tabsRef = ref(null)

const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuCustomer = ref(null)
const searchLoading = ref(false)
const addCustomerLoading = ref(false)

const cardColors = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
  'linear-gradient(135deg, #a18cd1, #fbc2eb)',
  'linear-gradient(135deg, #fccb90, #d57eeb)',
  'linear-gradient(135deg, #e0c3fc, #8ec5fc)',
]

const currentCustomerName = computed(() => {
  const c = customers.value.find(c => c.id === currentCustomerId.value)
  return c ? c.name : ''
})

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return projectList.value.slice(start, start + pageSize.value)
})

const uniqueHardwareVersions = computed(() => {
  return [...new Set(filterOptions.value.hardware_versions.filter(Boolean))]
})

const uniqueAndroidVersions = computed(() => {
  return [...new Set(filterOptions.value.android_versions.filter(Boolean))]
})

const uniqueScreenSizes = computed(() => {
  return [...new Set(filterOptions.value.screen_sizes.filter(Boolean))]
})

const uniqueTPs = computed(() => {
  return [...new Set(filterOptions.value.tps.filter(Boolean))]
})

const onTabsWheel = (e) => {
  if (!tabsRef.value) return
  tabsRef.value.scrollLeft += e.deltaY > 0 ? 120 : -120
}

const clearSearch = () => {
  searchText.value = ''
}

const loadCustomers = async () => {
  try {
    customers.value = await getCustomers()
  } catch (e) {
    ElMessage.error('加载客户列表失败')
  }
}

const selectCustomer = (id) => {
  if (editingCustomerId.value) return
  if (currentCustomerId.value === id) {
    currentCustomerId.value = null
  } else {
    currentCustomerId.value = id
  }
  currentPage.value = 1
  loadProjects()
  loadFilterOptions()
}

const loadProjects = async () => {
  searchLoading.value = true
  try {
    const params = {}
    if (currentCustomerId.value) params.customer = currentCustomerId.value
    if (searchText.value) params.search = searchText.value
    if (filterHardware.value.length > 0) params.hardware_version = filterHardware.value.join(',')
    if (filterAndroid.value.length > 0) params.android_version = filterAndroid.value.join(',')
    if (filterScreenSize.value.length > 0) params.screen_size = filterScreenSize.value.join(',')
    if (filterTP.value.length > 0) params.tp = filterTP.value.join(',')
    projectList.value = await getProjects(params)
  } catch (e) {
    ElMessage.error('加载项目列表失败')
  } finally {
    searchLoading.value = false
  }
}

const loadFilterOptions = async () => {
  try {
    const params = {}
    if (currentCustomerId.value) params.customer = currentCustomerId.value
    filterOptions.value = await getProjectFilterOptions(params)
  } catch (e) { /* 忽略 */ }
}

const resetFilters = () => {
  searchText.value = ''
  filterHardware.value = []
  filterAndroid.value = []
  filterScreenSize.value = []
  filterTP.value = []
  currentCustomerId.value = null
  currentPage.value = 1
  loadProjects()
  loadFilterOptions()
}

const handleAddCustomer = () => {
  showAddCustomerDialog.value = true
}

const confirmAddCustomer = async () => {
  if (!newCustomerName.value.trim()) {
    ElMessage.warning('请输入客户名称')
    return
  }
  addCustomerLoading.value = true
  try {
    await createCustomer({ name: newCustomerName.value.trim() })
    ElMessage.success('创建成功')
    showAddCustomerDialog.value = false
    newCustomerName.value = ''
    await loadCustomers()
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    addCustomerLoading.value = false
  }
}

const startEditCustomer = (c) => {
  editingCustomerId.value = c.id
  editingCustomerName.value = c.name
  nextTick(() => {
    if (editInputRef.value) {
      const inputs = Array.isArray(editInputRef.value) ? editInputRef.value : [editInputRef.value]
      inputs[0]?.focus()
    }
  })
}

const confirmEditCustomer = async () => {
  if (!editingCustomerName.value.trim()) {
    cancelEditCustomer()
    return
  }
  try {
    await updateCustomer(editingCustomerId.value, { name: editingCustomerName.value.trim() })
    ElMessage.success('重命名成功')
    editingCustomerId.value = null
    await loadCustomers()
    await loadProjects()
  } catch (e) {
    ElMessage.error('重命名失败')
  }
}

const cancelEditCustomer = () => {
  editingCustomerId.value = null
}

const showContextMenu = (event, c) => {
  contextMenuCustomer.value = c
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuVisible.value = true
}

const hideContextMenu = () => {
  contextMenuVisible.value = false
  contextMenuCustomer.value = null
}

const handleEditCustomerFromMenu = () => {
  if (contextMenuCustomer.value) {
    startEditCustomer(contextMenuCustomer.value)
  }
  hideContextMenu()
}

const handleDeleteCustomer = async () => {
  const c = contextMenuCustomer.value
  hideContextMenu()
  if (!c) return
  try {
    await ElMessageBox.confirm(
      `确定删除客户"${c.name}"？该客户下所有项目将一并删除。`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteCustomer(c.id)
    ElMessage.success('删除成功')
    if (currentCustomerId.value === c.id) {
      currentCustomerId.value = null
    }
    await loadCustomers()
    await loadProjects()
    await loadFilterOptions()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleAddProject = () => {
  editData.value = null
  showForm.value = true
}

const handleEdit = (row) => {
  editData.value = { ...row }
  showForm.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除项目"${row.project_name}"（序号${row.serial_number}）？删除后序号将自动重新编号。`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteProject(row.id)
    ElMessage.success('删除成功')
    await loadProjects()
    await loadFilterOptions()
    await loadCustomers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleViewDetail = (row) => {
  detailData.value = row
  showDetail.value = true
}

const onFormSaved = async () => {
  showForm.value = false
  await loadProjects()
  await loadFilterOptions()
  await loadCustomers()
}

const handleExport = () => {
  if (projectList.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = [
    '序号', '客户', '硬件版型', '项目名称', 'Android版本', '厂商', '型号',
    'Launcher', 'PIR', 'LED', '光感', 'WiFi',
    '屏幕尺寸', '屏幕型号', 'TP', '壳', '立项时间', '备注'
  ]
  const data = projectList.value.map(p => [
    p.serial_number, p.customer_name, p.hardware_version, p.project_name, p.android_version,
    p.brand, p.model, p.launcher, p.pir ? '有' : '无', p.led ? '有' : '无',
    p.light_sensor, p.wifi,
    p.screen_size, p.screen_model, p.tp, p.shell, p.project_establish_date, p.remarks
  ])
  const ws = XLSX.utils.aoa_to_sheet([headers, ...data])
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '项目配置表')
  const fileName = currentCustomerName.value
    ? `${currentCustomerName.value}_项目配置表`
    : `全部项目配置表`
  XLSX.writeFile(wb, `${fileName}_${new Date().toISOString().slice(0, 10)}.xlsx`)
  ElMessage.success('导出成功')
}

const FIELD_ALIAS_MAP = {
  '项目名称': 'project_name', '项目名': 'project_name', '名称': 'project_name',
  '硬件版型': 'hardware_version', '版型': 'hardware_version', '硬件版本': 'hardware_version',
  'android版本': 'android_version', '安卓版本': 'android_version', 'android': 'android_version', '安卓': 'android_version',
  '厂商': 'brand', '品牌': 'brand', '制造商': 'brand',
  '型号': 'model', '设备型号': 'model',
  'launcher': 'launcher', '启动器': 'launcher',
  'pir': 'pir', '人体感应': 'pir',
  'led': 'led', '指示灯': 'led',
  '光感': 'light_sensor', '光线传感器': 'light_sensor', '光传感器': 'light_sensor',
  'wifi': 'wifi', 'WiFi': 'wifi', '无线': 'wifi',
  '屏幕尺寸': 'screen_size', '屏尺寸': 'screen_size',
  '屏幕型号': 'screen_model', '屏型号': 'screen_model',
  'tp': 'tp', '触摸屏': 'tp', '触控': 'tp',
  '壳': 'shell', '外壳': 'shell', '机壳': 'shell',
  '立项时间': 'project_establish_date', '立项日期': 'project_establish_date', '创建时间': 'project_establish_date',
  '备注': 'remarks', '说明': 'remarks', '描述': 'remarks',
  '序号': 'serial_number', '编号': 'serial_number',
}

const BOOLEAN_FIELDS = ['pir', 'led']
const BOOLEAN_TRUE_VALUES = ['是', 'yes', 'true', '1', '✓', '有', 'y', 'on']
const BOOLEAN_FALSE_VALUES = ['否', 'no', 'false', '0', '✗', '无', 'n', 'off']

const CHOICE_FIELDS = {
  light_sensor: ['ADCF3', 'STK3311', '无'],
  wifi: ['2.4G', '5G'],
}

const DATE_FIELDS = ['project_establish_date']

const normalizeHeader = (h) => {
  return h.toString().trim().toLowerCase().replace(/[\s_\-·—]+/g, '')
}

const matchHeader = (header) => {
  const normalized = normalizeHeader(header)
  for (const [alias, field] of Object.entries(FIELD_ALIAS_MAP)) {
    if (normalizeHeader(alias) === normalized) return field
  }
  for (const [alias, field] of Object.entries(FIELD_ALIAS_MAP)) {
    if (normalizeHeader(alias).includes(normalized) || normalized.includes(normalizeHeader(alias))) return field
  }
  for (const [alias, field] of Object.entries(FIELD_ALIAS_MAP)) {
    const aliasNorm = normalizeHeader(alias)
    if (aliasNorm.charAt(0) === normalized.charAt(0) && aliasNorm.length <= 4) return field
  }
  return null
}

const convertBooleanValue = (val) => {
  const str = String(val).trim().toLowerCase()
  if (BOOLEAN_TRUE_VALUES.includes(str)) return true
  if (BOOLEAN_FALSE_VALUES.includes(str)) return false
  return null
}

const convertChoiceValue = (field, val) => {
  const str = String(val).trim()
  const choices = CHOICE_FIELDS[field]
  if (!choices) return str
  for (const c of choices) {
    if (c.toLowerCase() === str.toLowerCase()) return c
  }
  return str
}

const convertDateValue = (val) => {
  if (val === undefined || val === null) return ''
  if (typeof val === 'number') {
    const excelEpoch = new Date(1899, 11, 30)
    const date = new Date(excelEpoch.getTime() + val * 86400000)
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  }
  const str = String(val).trim()
  if (/^\d{4}-\d{1,2}-\d{1,2}$/.test(str)) {
    const parts = str.split('-')
    return `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`
  }
  if (/^\d{4}[\/\.]\d{1,2}[\/\.]\d{1,2}$/.test(str)) {
    const parts = str.split(/[\/\.]/)
    return `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`
  }
  return str
}

const showImportDialog = ref(false)
const importStep = ref(1)
const importFile = ref(null)
const importUploadRef = ref(null)
const importParsedData = ref([])
const importUnmatchedHeaders = ref([])
const importPreviewColumns = ref([])
const importLoading = ref(false)
const importResult = ref({ created: 0, updated: 0, skipped: 0, errors: [] })

const importResultTitle = computed(() => {
  const r = importResult.value
  if (r.created > 0 && r.skipped === 0) return '导入成功'
  if (r.created > 0 || r.updated > 0) return '导入完成（部分跳过）'
  if (r.skipped > 0 && r.created === 0 && r.updated === 0) return '导入完成（全部跳过）'
  return '导入完成'
})

const handleImportClick = () => {
  if (!currentCustomerId.value) {
    ElMessage.warning('请先选择一个客户')
    return
  }
  showImportDialog.value = true
  importStep.value = 1
}

const resetImportState = () => {
  importStep.value = 1
  importFile.value = null
  importParsedData.value = []
  importUnmatchedHeaders.value = []
  importPreviewColumns.value = []
  importLoading.value = false
  importResult.value = { created: 0, updated: 0, skipped: 0, errors: [] }
}

const handleImportFileChange = (file) => {
  importFile.value = file.raw
}

const parseImportFile = () => {
  if (!importFile.value) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[sheetName]
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

      const merges = worksheet['!merges'] || []
      for (const merge of merges) {
        const { s, e } = merge
        const col = s.c
        const startRow = s.r
        const endRow = e.r
        if (startRow === endRow) continue
        const fillValue = jsonData[startRow] ? jsonData[startRow][col] : undefined
        if (fillValue === undefined || fillValue === null) continue
        for (let r = startRow + 1; r <= endRow; r++) {
          if (!jsonData[r]) jsonData[r] = []
          while (jsonData[r].length <= col) jsonData[r].push(undefined)
          jsonData[r][col] = fillValue
        }
      }

      if (jsonData.length < 2) {
        ElMessage.warning('Excel 文件为空或只有表头')
        return
      }

      let headerRowIndex = 0
      let bestMatchCount = 0
      let bestFieldMapping = {}
      let bestUnmatched = []

      for (let ri = 0; ri < Math.min(3, jsonData.length); ri++) {
        const row = jsonData[ri]
        if (!row || row.length === 0) continue
        const testHeaders = row.map(h => String(h).trim())
        const testMapping = {}
        const testUnmatched = []
        let matchCount = 0

        testHeaders.forEach((header, idx) => {
          const field = matchHeader(header)
          if (field && !testMapping[field]) {
            testMapping[field] = idx
            matchCount++
          } else if (!field) {
            testUnmatched.push({ header, idx })
          }
        })

        if (matchCount > bestMatchCount) {
          bestMatchCount = matchCount
          headerRowIndex = ri
          bestFieldMapping = testMapping
          bestUnmatched = testUnmatched
        }
      }

      const fieldMapping = bestFieldMapping
      const unmatched = bestUnmatched
      importUnmatchedHeaders.value = unmatched.map(u => u.header)

      const parsedRows = []
      for (let i = headerRowIndex + 1; i < jsonData.length; i++) {
        const row = jsonData[i]
        if (!row || row.length === 0) continue
        const rowData = {}
        let hasMatch = false
        for (const [field, colIdx] of Object.entries(fieldMapping)) {
          let val = row[colIdx]
          if (val === undefined || val === null) continue
          if (BOOLEAN_FIELDS.includes(field)) {
            const boolVal = convertBooleanValue(val)
            if (boolVal !== null) {
              rowData[field] = boolVal
              hasMatch = true
            }
          } else if (DATE_FIELDS.includes(field)) {
            const dateVal = convertDateValue(val)
            if (dateVal) {
              rowData[field] = dateVal
              hasMatch = true
            }
          } else if (CHOICE_FIELDS[field]) {
            rowData[field] = convertChoiceValue(field, val)
            hasMatch = true
          } else {
            rowData[field] = String(val).trim()
            if (rowData[field]) hasMatch = true
          }
        }
        for (const u of unmatched) {
          const val = row[u.idx]
          if (val !== undefined && val !== null && String(val).trim()) {
            rowData[`_unmatched_${u.idx}`] = String(val).trim()
          }
        }
        if (hasMatch && rowData.project_name && rowData.project_name.trim()) {
          parsedRows.push(rowData)
        }
      }

      importParsedData.value = parsedRows

      const previewCols = Object.keys(fieldMapping).map(f => ({
        key: f,
        label: allColumns.find(c => c.key === f)?.label || f,
        unmatched: false,
      }))
      for (const u of unmatched) {
        previewCols.push({
          key: `_unmatched_${u.idx}`,
          label: u.header,
          unmatched: true,
        })
      }
      importPreviewColumns.value = previewCols

      if (unmatched.length > 0) {
        ElMessage.warning(`以下列未识别：${unmatched.join('、')}`)
      }

      importStep.value = 2
    } catch (err) {
      console.error('解析Excel失败:', err)
      ElMessage.error('解析 Excel 文件失败，请检查文件格式')
    }
  }
  reader.readAsArrayBuffer(importFile.value)
}

const executeImport = async () => {
  if (!currentCustomerId.value) {
    ElMessage.error('请先选择客户')
    return
  }

  const existingMap = {}
  projectList.value.forEach(p => {
    const key = `${p.project_name}|||${p.hardware_version || ''}`
    existingMap[key] = p
  })

  const duplicates = importParsedData.value.filter(row => {
    const key = `${row.project_name}|||${row.hardware_version || ''}`
    return !!existingMap[key]
  })

  let overwrite = false
  if (duplicates.length > 0) {
    try {
      await ElMessageBox.confirm(
        `以下项目名称和版型均已存在：${duplicates.map(d => `【${d.project_name}】`).join('、')}，是否覆盖更新？选择"否"将跳过这些记录。`,
        '重复项目检测',
        { confirmButtonText: '是（覆盖更新）', cancelButtonText: '否（跳过）', type: 'warning' }
      )
      overwrite = true
    } catch {
      overwrite = false
    }
  }

  const items = importParsedData.value.map(row => {
    const key = `${row.project_name}|||${row.hardware_version || ''}`
    return {
      ...row,
      _overwrite: overwrite && !!existingMap[key],
    }
  })

  importLoading.value = true
  try {
    const result = await batchImportProjects({
      customer_id: currentCustomerId.value,
      items,
    })
    importResult.value = result
    importStep.value = 3
    await loadProjects()
    await loadFilterOptions()
    await loadCustomers()
  } catch (err) {
    console.error('导入失败:', err)
    ElMessage.error('导入失败，请检查数据格式')
  } finally {
    importLoading.value = false
  }
}

onMounted(async () => {
  await loadCustomers()
  await loadProjects()
  await loadFilterOptions()
  document.addEventListener('click', hideContextMenu)

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          observer.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.1 }
  )
  document.querySelectorAll('.scroll-reveal').forEach((el) => {
    observer.observe(el)
  })
  const revealObserver = new MutationObserver(() => {
    document.querySelectorAll('.scroll-reveal:not(.revealed)').forEach((el) => {
      observer.observe(el)
    })
  })
  revealObserver.observe(document.querySelector('.project-page'), {
    childList: true,
    subtree: true,
  })
})

/* ===== 配置雷达 - 检索 ===== */
const radarLoading = ref(false)
const radarDone = ref(false)
const radarResults = ref([])
const radarError = ref('')

const handleRadarSearch = async () => {
  radarLoading.value = true
  radarDone.value = false
  radarError.value = ''
  radarResults.value = []
  try {
    const res = await searchProjects()
    if (res.code === 200) {
      radarResults.value = res.data
    } else {
      radarError.value = res.message || '检索失败'
    }
  } catch (err) {
    radarError.value = '检索请求失败，请检查后端服务是否正常'
    console.error('配置雷达检索失败:', err)
  } finally {
    radarLoading.value = false
    radarDone.value = true
  }
}

const handleRadarSort = ({ prop, order }) => {
  if (!prop || !order) return
  const sorted = [...radarResults.value]
  sorted.sort((a, b) => {
    const va = a[prop] || ''
    const vb = b[prop] || ''
    const cmp = va.localeCompare(vb, 'zh-CN')
    return order === 'ascending' ? cmp : -cmp
  })
  radarResults.value = sorted
}

const copyRadarPath = (path) => {
  navigator.clipboard.writeText(path).then(() => {
    ElMessage.success('路径已复制')
  }).catch(() => {
    ElMessage.warning('请手动复制路径')
  })
}

/* ===== 数据同步 ===== */
const syncing = ref(false)
const syncLogs = ref([])
const syncSummary = ref(null)
const syncError = ref('')
const logWindowRef = ref(null)

const handleSync = async () => {
  syncing.value = true
  syncLogs.value = []
  syncSummary.value = null
  syncError.value = ''

  executeDataSync(
    // onLog: 实时日志
    (data) => {
      let message = ''
      const status = data.status
      if (data.status === 'success') {
        message = `[${data.projectName}] 同步成功`
      } else if (data.status === 'skipped') {
        message = `[${data.projectName}] 跳过同步 - ${data.reason}`
      } else if (data.status === 'failed') {
        message = `[${data.projectName}] 导入失败 - ${data.reason}`
      } else {
        message = `[${data.projectName}] 检索完成`
      }
      syncLogs.value.push({ message, status, projectName: data.projectName })
      nextTick(() => {
        if (logWindowRef.value) {
          logWindowRef.value.scrollTop = logWindowRef.value.scrollHeight
        }
      })
    },
    // onComplete: 汇总报告
    (data) => {
      syncSummary.value = data
      syncing.value = false
      nextTick(() => {
        if (logWindowRef.value) {
          logWindowRef.value.scrollTop = logWindowRef.value.scrollHeight
        }
      })
    },
    // onError: 请求失败
    (msg) => {
      syncError.value = msg
      syncing.value = false
    }
  )
}

onBeforeUnmount(() => {
  document.removeEventListener('click', hideContextMenu)
})
</script>

<style scoped>
.project-page {
  height: 100%;
  max-width: 1400px;
}
.page-header {
  margin-bottom: 20px;
  text-align: center;
}
.page-title {
  margin: 0;
  font-family: 'Noto Serif SC', 'SimSun', 'STSong', serif;
  font-size: 2.25rem;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: 0.25em;
}
.filter-card {
  padding: 24px;
  margin-bottom: 12px;
}

.search-bar {
  display: flex;
  align-items: center;
}

.search-input-box {
  position: relative;
  width: 85%;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  width: 14px;
  height: 14px;
  color: #666;
  z-index: 1;
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 32px 0 38px;
  border: 2px solid #C4C7CE;
  border-right: none;
  border-radius: 10px 0 0 10px;
  font-size: 14px;
  color: #333;
  background: #FFFFFF;
  transition: border-color 0.2s ease;
  outline: none;
}

.search-input::placeholder {
  color: #999;
}

.search-input:hover {
  border-color: #9195A3;
}

.search-input:focus {
  border-color: #3385FF;
}

.search-clear {
  position: absolute;
  right: 8px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #999;
  cursor: pointer;
  border-radius: 50%;
  transition: background 0.15s;
}

.search-clear:hover {
  background: #F5F5F5;
  color: #666;
}

.search-btn {
  width: 15%;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3385FF 0%, #2A75FF 100%);
  color: #FFFFFF;
  border: none;
  border-radius: 0 10px 10px 0;
  font-size: 16px;
  font-weight: 700;
  font-family: "Source Han Sans", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 2px;
}

.search-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(51, 133, 255, 0.4);
}

.search-btn:active {
  transform: scale(0.98);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  justify-content: flex-end;
}

.filter-select {
  width: 100px;
}

.filter-select-screen {
  width: 130px;
}

.filter-select-multi {
  width: 130px;
}

.filter-select :deep(.el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #E0E0E0;
  box-shadow: none !important;
  height: 28px;
}

.filter-select :deep(.el-input__wrapper:hover) {
  border-color: #3385FF;
}

.filter-select :deep(.el-input__wrapper.is-focus) {
  border-color: #3385FF;
  box-shadow: 0 0 0 1px #3385FF inset !important;
}

.filter-select :deep(.el-input__inner) {
  font-size: 12px;
  height: 26px;
  line-height: 26px;
}

.filter-select :deep(.el-select__tags) {
  max-height: 24px;
}

.filter-select :deep(.el-tag) {
  max-height: 18px;
  font-size: 11px;
}

.filter-select :deep(.el-select__placeholder) {
  font-size: 12px;
}

.filter-select :deep(.el-input__suffix) {
  font-size: 12px;
}

.filter-select :deep(.el-select__icon) {
  font-size: 12px;
  width: 14px;
}

.reset-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: 60px;
  height: 28px;
  background: #F5F5F5;
  color: #FF4D4F;
  border: 1px solid #E0E0E0;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.reset-btn:hover {
  background: #FFF1F0;
  border-color: #FFCCC7;
}

.reset-icon {
  font-size: 12px;
}
.customer-cards-wrapper {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 50%, #e0e7ff 100%);
  border-radius: 12px;
  padding: 16px;
  overflow: hidden;
}
.customer-cards {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}
.customer-cards::-webkit-scrollbar {
  display: none;
}
.customer-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: #FFFFFF;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  min-width: 160px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 2px solid transparent;
  user-select: none;
}
.customer-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}
.customer-card.active {
  border-color: #2563EB;
  box-shadow: 0 4px 16px rgba(37,99,235,0.2);
}
.card-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}
.card-icon-add {
  background: linear-gradient(135deg, #94a3b8, #64748b) !important;
}
.card-edit-input {
  border: none;
  outline: none;
  background: transparent;
  color: #FFFFFF;
  font-size: 16px;
  font-weight: 700;
  width: 24px;
  text-align: center;
}
.card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.card-label {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}
.card-number {
  font-size: 12px;
  color: #94A3B8;
}
.card-add {
  border: 2px dashed #CBD5E1;
  background: rgba(255,255,255,0.6);
}
.card-add:hover {
  border-color: #2563EB;
  background: rgba(255,255,255,0.9);
}
.table-section {
  flex: 1;
}
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.table-customer-label {
  font-size: 15px;
  font-weight: 600;
  color: #0F172A;
}
.table-actions {
  display: flex;
  gap: 8px;
}
.table-card {
  background: #FFFFFF;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  padding: 20px;
}
.pagination-area {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.column-settings-body {
  padding: 4px 0;
}
.column-settings-tip {
  font-size: 12px;
  color: #94A3B8;
  margin-bottom: 16px;
}
.column-settings-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.column-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  background: #F8FAFC;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 13px;
  color: #64748B;
  user-select: none;
}
.column-chip:hover {
  border-color: #93C5FD;
  background: #EFF6FF;
}
.column-chip.active {
  background: #2563EB;
  border-color: #2563EB;
  color: #FFFFFF;
}
.chip-check {
  font-size: 12px;
}
.context-menu {
  position: fixed;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 4px;
  z-index: 9999;
}
.context-menu-item {
  padding: 8px 16px;
  font-size: 13px;
  color: #334155;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.1s;
}
.context-menu-item:hover {
  background: #F8FAFC;
}
.context-menu-item.danger {
  color: #EF4444;
}
.context-menu-item.danger:hover {
  background: #FEF2F2;
}

.scroll-reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.5s ease, transform 0.5s ease;
  transition-delay: var(--reveal-delay, 0ms);
}

.scroll-reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}

.btn-spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.search-btn.is-loading {
  pointer-events: none;
  opacity: 0.85;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.import-body {
  min-height: 200px;
}
.import-step {
  padding: 8px 0;
}
.import-upload {
  width: 100%;
}
.import-upload :deep(.el-upload-dragger) {
  width: 100%;
  border-radius: 12px;
  border: 2px dashed #CBD5E1;
  transition: border-color 0.2s;
}
.import-upload :deep(.el-upload-dragger:hover) {
  border-color: #2563EB;
}
.import-preview-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #334155;
}
.import-unmatched {
  color: #F59E0B;
  font-size: 12px;
}
.import-preview-table-wrapper {
  border-radius: 8px;
  overflow: hidden;
}
.import-preview-more {
  text-align: center;
  font-size: 12px;
  color: #94A3B8;
  padding: 8px 0;
}
.import-result {
  padding: 16px 0;
}
.import-result-detail {
  font-size: 14px;
  color: #475569;
  line-height: 2;
}
.import-result-detail p {
  margin: 0;
}
.import-result-detail strong {
  color: #0F172A;
}
.import-result-errors {
  margin-top: 8px;
  text-align: left;
}
.import-result-errors p {
  font-weight: 600;
  color: #F59E0B;
  margin-bottom: 4px;
}
.import-result-errors ul {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: #64748B;
}
.import-result-errors li {
  line-height: 1.8;
}

.import-preview-table-wrapper :deep(.unmatched-header) {
  background: #F1F5F9 !important;
  color: #94A3B8 !important;
}

.import-preview-table-wrapper :deep(.unmatched-col) {
  background: #F8FAFC;
  color: #94A3B8;
}

.unmatched-label {
  color: #94A3B8;
  text-decoration: line-through;
  text-decoration-color: #CBD5E1;
}

.unmatched-tag {
  margin-left: 4px;
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 4px;
}

/* ===== 配置雷达模块 ===== */
.concert-section {
  margin-top: 48px;
  padding: 32px 24px 48px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
}
.concert-header {
  text-align: center;
  margin-bottom: 48px;
}
.concert-title {
  margin: 0 0 8px 0;
  font-family: 'Noto Serif SC', 'SimSun', 'STSong', serif;
  font-size: 2.25rem;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: 0.25em;
}
.concert-subtitle {
  margin: 0;
  font-family: 'Noto Sans SC', -apple-system, sans-serif;
  font-size: 13px;
  font-weight: 300;
  color: #C9A96E;
  letter-spacing: 0.35em;
}

/* ===== 配置雷达 - 检索区域 ===== */
.concert-search-bar {
  text-align: center;
  margin-bottom: 24px;
}
.concert-search-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 36px;
  background: #C9A96E;
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 2px;
  min-width: 140px;
}
.concert-search-btn:hover {
  background: #B8944F;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(201, 169, 110, 0.4);
}
.concert-search-btn:active {
  transform: translateY(0);
}
.concert-search-btn.is-loading {
  opacity: 0.85;
  pointer-events: none;
}
.concert-search-btn:disabled {
  opacity: 0.85;
  cursor: not-allowed;
}
.concert-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: concert-spin 0.6s linear infinite;
}
@keyframes concert-spin {
  to { transform: rotate(360deg); }
}
.concert-results {
  margin-top: 24px;
}
.concert-results :deep(.el-table th.el-table__cell) {
  background-color: #fafafa;
  color: #1a1a1a;
  font-weight: 600;
}
.concert-results :deep(.el-table th.el-table__cell > .cell) {
  letter-spacing: 0.04em;
}
.concert-result-count {
  text-align: right;
  font-size: 13px;
  color: #999;
  margin-top: 12px;
  padding-right: 8px;
}
.concert-empty {
  margin-top: 32px;
}
.concert-error {
  margin-top: 16px;
}

/* ===== 数据同步模块 ===== */
.sync-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.sync-btn-wrapper {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
.sync-btn {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100px;
  height: 100px;
  background: #C9A96E;
  color: #FFFFFF;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 1px;
}
.sync-btn:hover {
  background: #B8944F;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(201, 169, 110, 0.4);
}
.sync-btn:active {
  transform: translateY(0);
}
.sync-btn.is-loading {
  opacity: 0.85;
  pointer-events: none;
}
.sync-btn:disabled {
  opacity: 0.85;
  cursor: not-allowed;
}
.sync-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: sync-spin 0.6s linear infinite;
}
@keyframes sync-spin {
  to { transform: rotate(360deg); }
}
.sync-log-window {
  flex: 1;
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  font-size: 13px;
  line-height: 1.8;
}
.sync-log-placeholder {
  color: #ccc;
  text-align: center;
  padding: 60px 0;
  font-size: 14px;
}
.sync-log-item {
  padding: 4px 0;
  animation: sync-fadeInDown 0.3s ease;
}
.sync-log-icon {
  margin-right: 6px;
}
.sync-log-text {
  color: #333;
}
.sync-log-success .sync-log-text {
  color: #52c41a;
}
.sync-log-failed .sync-log-text {
  color: #ff4d4f;
}
.sync-log-skipped .sync-log-text {
  color: #d4a017;
}
.sync-log-info .sync-log-text {
  color: #1890ff;
}
.sync-summary {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
}
.sync-summary-divider {
  text-align: center;
  color: #C9A96E;
  font-size: 12px;
  letter-spacing: 0.2em;
  margin-bottom: 8px;
}
.sync-summary-item {
  font-size: 13px;
  color: #333;
  line-height: 2;
}
.sync-summary-sub {
  display: block;
  font-size: 12px;
  color: #888;
  padding-left: 16px;
  line-height: 1.8;
}
.sync-error-bar {
  color: #ff4d4f;
  padding: 8px;
  margin-top: 8px;
  background: #fff2f0;
  border-radius: 4px;
  font-size: 13px;
}
@keyframes sync-fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
