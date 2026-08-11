<template>
  <div class="fade-in workbench-page-shell iac-page-shell">
    <section class="hero panel iac-hero">
      <div class="release-hero-copy">
        <div class="release-hero-title-row release-hero-title-inline">
          <span class="release-header-icon iac-header-icon"><el-icon><SetUp /></el-icon></span>
          <h2>IaC 方案</h2>
          <p class="subtitle inline-subtitle iac-hero-desc">基于 Terraform 管理阿里云 / 华为云基础设施，支持渲染、下载、执行与 CMDB 同步。</p>
        </div>
      </div>
    </section>

    <div class="audit-grid iac-top-stats">
      <div v-for="card in summaryCards" :key="card.label" class="audit-card audit-card--inline iac-summary-card" :class="card.tone">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value">{{ card.value }}</div>
      </div>
    </div>

    <div class="neo-tabs theme-blue iac-main-tabs">
      <button v-for="tab in mainTabs" :key="tab.key" class="neo-tab-btn" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        <el-icon style="margin-right:4px;"><component :is="tab.icon" /></el-icon>
        {{ tab.label }}
      </button>
    </div>

    <!-- 方案列表 -->
    <div v-if="activeTab === 'stacks'" class="workbench-card iac-stack-card">
      <div class="section-toolbar">
        <div class="toolbar-head">
          <span class="toolbar-title">方案列表</span>
          <span class="toolbar-desc">已渲染并可执行的 Terraform 基础设施方案。</span>
        </div>
        <div class="workbench-card-actions">
          <el-button class="filter-refresh-btn" @click="fetchStacks">
            <el-icon><RefreshRight /></el-icon>
            刷新
          </el-button>
          <el-button v-if="canManageIac" class="filter-refresh-btn" type="primary" @click="openCreate">
            <el-icon><Plus /></el-icon>
            新建方案
          </el-button>
        </div>
      </div>

      <div class="workbench-toolbar workbench-toolbar--history iac-stack-toolbar">
        <div class="workbench-toolbar-left">
          <el-input v-model="searchKeyword" clearable placeholder="搜索方案名称、描述、云厂商、区域" style="width: 320px" />
        </div>
        <div class="workbench-toolbar-right">
          <el-tag size="large" type="info">方案总数 {{ stacks.length }}</el-tag>
          <el-tag size="large" type="success">成功 {{ stackStats.success }}</el-tag>
          <el-tag size="large" type="danger">失败 {{ stackStats.failed }}</el-tag>
        </div>
      </div>

      <el-table :data="filteredStacks" stripe v-loading="loading" style="width:100%" class="iac-stack-table">
        <el-table-column label="方案名称" min-width="180">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px;cursor:pointer;" @click="openDetail(row)">
              <el-icon color="#2563eb"><Box /></el-icon>
              <span style="font-weight:600">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="provider_label" label="云厂商" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.provider_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="区域" width="120" />
        <el-table-column label="资源" width="80" align="center">
          <template #default="{ row }">{{ row.resource_count }}</template>
        </el-table-column>
        <el-table-column label="最近执行" width="130">
          <template #default="{ row }">
            <el-tag :type="executionTagType(row.last_execution_status)" size="small">
              {{ executionStatusLabel(row.last_execution_status, row.last_execution_action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="CMDB 同步" width="150">
          <template #default="{ row }">
            <span v-if="row.last_cmdb_sync_at">{{ formatTime(row.last_cmdb_sync_at) }}</span>
            <span v-else class="muted-text">未同步</span>
          </template>
        </el-table-column>
        <el-table-column label="创建人" prop="created_by" width="100" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="canManageIac" link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="canExecuteIac" link type="success" size="small" @click="openExecute(row)">执行</el-button>
            <el-button v-if="canManageIac" link type="warning" size="small" @click="syncCmdb(row)">同步 CMDB</el-button>
            <el-button v-if="canManageIac" link type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !filteredStacks.length" class="empty-state">
        <div class="empty-icon">⇆</div>
        <div class="empty-text">暂无 Terraform 方案，点击右上角「新建方案」开始。</div>
      </div>
    </div>

    <!-- 新建 / 编辑方案 -->
    <div v-else-if="activeTab === 'create'" class="workbench-card iac-form-card">
      <div class="section-toolbar">
        <div class="toolbar-head">
          <span class="toolbar-title">{{ editingId ? '编辑方案' : '新建方案' }}</span>
          <span class="toolbar-desc">选择云厂商、区域与资源配置，系统自动渲染 Terraform 工程。</span>
        </div>
        <div class="workbench-card-actions">
          <el-button class="filter-refresh-btn" @click="switchTab('stacks')">返回列表</el-button>
        </div>
      </div>

      <el-form :model="form" label-width="110px" v-loading="formLoading" class="iac-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="方案名称" required>
              <el-input v-model="form.name" placeholder="例如 prod-web" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="云厂商" required>
              <el-select v-model="form.cloud_provider" placeholder="选择云厂商" style="width:100%" @change="onProviderChange">
                <el-option v-for="(meta, key) in catalog" :key="key" :label="meta.label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="区域">
              <el-select v-model="form.region" placeholder="选择区域" style="width:100%" @change="onRegionChange">
                <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="可用区">
              <el-select v-model="form.zone" placeholder="选择可用区" style="width:100%">
                <el-option v-for="z in zoneOptions" :key="z.value" :label="z.label" :value="z.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="描述">
              <el-input v-model="form.description" placeholder="方案描述（可选）" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">资源配置</el-divider>
        <el-row :gutter="16">
          <el-col v-for="section in formSections" :key="section.key" :span="12">
            <el-divider :content-position="'left'">
              <span class="section-divider-label">{{ section.label }}</span>
            </el-divider>
            <el-form-item
              v-for="field in section.fields"
              :key="field.path"
              :label="field.label"
            >
              <el-input-number
                v-if="field.type === 'number'"
                :model-value="configValue(field.path)"
                :min="field.min"
                :max="field.max"
                style="width:100%"
                @update:model-value="(v) => setConfigValue(field.path, v)"
              />
              <el-switch
                v-else-if="field.type === 'switch'"
                :model-value="configValue(field.path)"
                active-text="启用"
                inactive-text="停用"
                @update:model-value="(v) => setConfigValue(field.path, v)"
              />
              <el-select
                v-else-if="field.type === 'select'"
                :model-value="configValue(field.path)"
                style="width:100%"
                @update:model-value="(v) => setConfigValue(field.path, v)"
              >
                <el-option
                  v-for="opt in field.options"
                  :key="typeof opt === 'object' ? opt.value : opt"
                  :label="typeof opt === 'object' ? opt.label : opt"
                  :value="typeof opt === 'object' ? opt.value : opt"
                />
              </el-select>
              <el-select
                v-else-if="field.type === 'ports'"
                :model-value="configValue(field.path)"
                multiple
                allow-create
                filterable
                placeholder="输入端口后回车"
                style="width:100%"
                @update:model-value="(v) => setConfigValue(field.path, v)"
              >
                <el-option v-for="p in defaultPorts" :key="p" :label="p" :value="p" />
              </el-select>
              <el-input
                v-else
                :model-value="configValue(field.path)"
                :placeholder="field.label"
                @update:model-value="(v) => setConfigValue(field.path, v)"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="iac-form-actions">
          <el-button @click="switchTab('stacks')">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveStack">
            {{ editingId ? '保存' : '创建并渲染' }}
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="方案详情" width="760px" top="6vh" append-to-body class="iac-detail-dialog">
      <div v-if="detail" v-loading="detailLoading">
        <div class="iac-detail-head">
          <div class="iac-detail-title">
            <el-icon color="#2563eb"><Box /></el-icon>
            <span>{{ detail.name }}</span>
            <el-tag size="small" effect="plain" style="margin-left:8px;">{{ detail.provider_label }}</el-tag>
          </div>
          <div class="iac-detail-meta">
            <span>{{ detail.region }} / {{ detail.zone }}</span>
            <span class="muted-text">{{ detail.description }}</span>
          </div>
        </div>

        <el-descriptions :column="2" border class="iac-detail-desc">
          <el-descriptions-item label="资源数量">{{ detail.resource_count }}</el-descriptions-item>
          <el-descriptions-item label="CMDB 绑定">{{ detail.binding_count }}</el-descriptions-item>
          <el-descriptions-item label="最近执行">
            {{ executionStatusLabel(detail.last_execution_status, detail.last_execution_action) }}
          </el-descriptions-item>
          <el-descriptions-item label="最近同步">
            <span v-if="detail.last_cmdb_sync_at">{{ formatTime(detail.last_cmdb_sync_at) }}</span>
            <span v-else class="muted-text">未同步</span>
          </el-descriptions-item>
          <el-descriptions-item label="生成文件" :span="2">
            <el-tag v-for="f in detail.generated_file_names" :key="f" size="small" class="iac-file-tag">{{ f }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="iac-detail-section-title">执行记录</div>
        <el-table :data="executions" size="small" v-loading="executionsLoading" style="width:100%">
          <el-table-column prop="action_label" label="动作" width="80" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="executionTagType(row.status)" size="small">{{ row.status_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="时间" width="160">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="created_by" label="执行人" width="90" />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="viewExecution(row)">日志</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="iac-detail-actions">
          <el-button @click="downloadStack(detail)"><el-icon><Download /></el-icon>下载工程</el-button>
          <el-button v-if="canExecuteIac" type="success" @click="openExecute(detail)"><el-icon><CaretRight /></el-icon>执行</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 执行弹窗 -->
    <el-dialog v-model="executeVisible" title="执行 Terraform 方案" width="560px" append-to-body>
      <el-form :model="executeForm" label-width="120px">
        <el-form-item label="方案">
          <span style="font-weight:600">{{ currentStack?.name }}</span>
        </el-form-item>
        <el-form-item label="执行动作">
          <el-select v-model="executeForm.action" style="width:100%">
            <el-option label="init（初始化）" value="init" />
            <el-option label="plan（计划）" value="plan" />
            <el-option label="apply（执行）" value="apply" />
            <el-option label="destroy（销毁）" value="destroy" />
          </el-select>
        </el-form-item>
        <el-alert
          v-if="executeForm.action !== 'init'"
          title="执行 plan / apply / destroy 需要填写云账号凭证，将用于生成 terraform.tfvars"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom:16px;"
        />
        <template v-if="executeForm.action !== 'init'">
          <el-form-item v-for="secret in secretFields" :key="secret.key" :label="secret.label">
            <el-input
              v-model="executeForm.secrets[secret.key]"
              type="password"
              show-password
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="executeVisible = false">取消</el-button>
        <el-button type="primary" :loading="executing" @click="submitExecute">确认执行</el-button>
      </template>
    </el-dialog>

    <!-- 执行日志弹窗 -->
    <el-dialog v-model="logVisible" title="执行日志" width="720px" top="6vh" append-to-body>
      <div class="iac-log-panel">
        <div class="iac-log-meta">
          <el-tag :type="executionTagType(logDetail?.status)" size="small">{{ logDetail?.status_label }}</el-tag>
          <span v-if="logDetail?.command" class="iac-log-command">{{ logDetail.command }}</span>
        </div>
        <pre v-if="logDetail?.stdout" class="iac-log-block">{{ logDetail.stdout }}</pre>
        <pre v-if="logDetail?.stderr" class="iac-log-block iac-log-stderr">{{ logDetail.stderr }}</pre>
        <div v-if="!logDetail?.stdout && !logDetail?.stderr" class="empty-state">
          <div class="empty-text">暂无输出</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  SetUp,
  RefreshRight,
  Plus,
  Box,
  Download,
  CaretRight,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  getIaCStacks,
  getIaCStack,
  createIaCStack,
  updateIaCStack,
  deleteIaCStack,
  downloadIaCStack,
  getIaCStackExecutions,
  executeIaCStack,
  syncIaCStackCmdb,
  getIaCCatalog,
} from '@/api/modules/iac'

const stacks = ref([])
const loading = ref(false)
const activeTab = ref('stacks')
const searchKeyword = ref('')
const catalog = ref({})
const formLoading = ref(false)
const saving = ref(false)
const editingId = ref(null)
const executing = ref(false)
const currentStack = ref(null)
const executeVisible = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const executions = ref([])
const executionsLoading = ref(false)
const logVisible = ref(false)
const logDetail = ref(null)

const defaultPorts = [22, 80, 443]

const form = reactive({
  name: '',
  description: '',
  cloud_provider: '',
  region: '',
  zone: '',
  config: {},
})

const executeForm = reactive({
  action: 'init',
  secrets: {},
})

const mainTabs = [
  { key: 'stacks', label: '方案列表', icon: Box },
  { key: 'create', label: '新建方案', icon: Plus },
]

const canManageIac = ref(false)
const canExecuteIac = ref(false)

const stackStats = computed(() => ({
  success: stacks.value.filter(s => s.last_execution_status === 'success').length,
  failed: stacks.value.filter(s => s.last_execution_status === 'failed').length,
}))

const summaryCards = computed(() => [
  { label: '方案总数', value: stacks.value.length, tone: '' },
  { label: '执行成功', value: stackStats.value.success, tone: 'success-tone' },
  { label: '执行失败', value: stackStats.value.failed, tone: 'danger-tone' },
  { label: '已同步 CMDB', value: stacks.value.filter(s => s.last_cmdb_sync_at).length, tone: 'info-tone' },
])

const filteredStacks = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return stacks.value
  return stacks.value.filter((s) =>
    [s.name, s.description, s.provider_label, s.region, s.zone]
      .filter(Boolean)
      .some(v => String(v).toLowerCase().includes(keyword))
  )
})

const providerMeta = computed(() => catalog.value[form.cloud_provider] || null)
const regionOptions = computed(() => providerMeta.value?.regions || [])
const zoneOptions = computed(() => {
  const region = form.region
  if (!providerMeta.value?.zone_options || !region) return []
  return providerMeta.value.zone_options[region] || []
})
const formSections = computed(() => providerMeta.value?.sections || [])

const secretFields = computed(() => {
  const provider = form.cloud_provider || currentStack.value?.cloud_provider || ''
  if (provider === 'aliyun') {
    return [
      { key: 'alicloud_access_key', label: 'Access Key' },
      { key: 'alicloud_secret_key', label: 'Secret Key' },
    ]
  }
  if (provider === 'huaweicloud') {
    return [
      { key: 'huaweicloud_access_key', label: 'Access Key' },
      { key: 'huaweicloud_secret_key', label: 'Secret Key' },
    ]
  }
  return []
})

function getByPath(obj, path) {
  return path.split('.').reduce((acc, key) => (acc == null ? acc : acc[key]), obj)
}
function setByPath(obj, path, value) {
  const keys = path.split('.')
  let target = obj
  for (let i = 0; i < keys.length - 1; i += 1) {
    if (target[keys[i]] == null) target[keys[i]] = {}
    target = target[keys[i]]
  }
  target[keys[keys.length - 1]] = value
}
function configValue(path) {
  return getByPath(form.config, path)
}
function setConfigValue(path, value) {
  setByPath(form.config, path, value)
}

function switchTab(key) {
  if (key === 'create' && !Object.keys(catalog.value).length) {
    ElMessage.warning('云厂商目录尚未加载，请稍后重试')
    return
  }
  if (key === 'create' && activeTab.value !== 'create') {
    resetForm()
  }
  activeTab.value = key
}

function resetForm() {
  editingId.value = null
  form.name = ''
  form.description = ''
  form.cloud_provider = ''
  form.region = ''
  form.zone = ''
  form.config = {}
}

function onProviderChange(provider) {
  const meta = catalog.value[provider]
  form.config = JSON.parse(JSON.stringify(meta?.defaults || {}))
  form.region = meta?.regions?.[0]?.value || ''
  onRegionChange()
}

function onRegionChange() {
  const meta = providerMeta.value
  if (!meta?.zone_options || !form.region) return
  form.zone = meta.zone_options[form.region]?.[0]?.value || ''
}

function executionStatusLabel(status, action) {
  if (!status) return '未执行'
  const map = { success: '成功', failed: '失败', pending: '待执行', running: '执行中' }
  const actionMap = { init: 'init', plan: 'plan', apply: 'apply', destroy: 'destroy' }
  return action ? `${map[status] || status} (${actionMap[action] || action})` : (map[status] || status)
}
function executionTagType(status) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'running') return 'warning'
  return 'info'
}

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function loadPermissions() {
  const authStore = useAuthStore()
  canManageIac.value = authStore.hasAnyPermission(['ops.iac.manage'])
  canExecuteIac.value = authStore.hasAnyPermission(['ops.iac.execute'])
}

async function fetchCatalog() {
  try {
    const data = await getIaCCatalog()
    catalog.value = data.providers || data || {}
  } catch (e) {
    // 错误由拦截器统一提示
  }
}

async function fetchStacks() {
  loading.value = true
  try {
    stacks.value = await getIaCStacks()
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

function openCreate() {
  if (!Object.keys(catalog.value).length) {
    ElMessage.warning('云厂商目录尚未加载，请稍后重试')
    return
  }
  resetForm()
  switchTab('create')
}

function openDetail(row) {
  detailVisible.value = true
  detail.value = row
  detailLoading.value = true
  executionsLoading.value = true
  getIaCStack(row.id).then((data) => { detail.value = data }).finally(() => { detailLoading.value = false })
  getIaCStackExecutions(row.id).then((data) => { executions.value = data }).finally(() => { executionsLoading.value = false })
}

async function openEdit(row) {
  if (!Object.keys(catalog.value).length) {
    ElMessage.warning('云厂商目录尚未加载，请稍后重试')
    return
  }
  formLoading.value = true
  try {
    const data = await getIaCStack(row.id)
    editingId.value = data.id
    form.name = data.name || ''
    form.description = data.description || ''
    form.cloud_provider = data.cloud_provider || ''
    form.region = data.region || ''
    form.zone = data.zone || ''
    form.config = JSON.parse(JSON.stringify(data.config || {}))
    if (!form.config.metadata) form.config.metadata = {}
    form.config.metadata.project_name = form.config.metadata.project_name || data.name
    activeTab.value = 'create'
  } catch (e) {
    // 拦截器已提示
  } finally {
    formLoading.value = false
  }
}

async function downloadStack(row) {
  try {
    const blob = await downloadIaCStack(row.id)
    triggerDownload(blob, `${row.name}-terraform.zip`)
  } catch (e) {
    // 拦截器已提示
  }
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function saveStack() {
  const meta = providerMeta.value
  if (!form.name) {
    ElMessage.warning('请填写方案名称')
    return
  }
  if (!meta) {
    ElMessage.warning('请选择云厂商')
    return
  }
  saving.value = true
  try {
    const config = JSON.parse(JSON.stringify(form.config || {}))
    if (!config.metadata) config.metadata = {}
    config.metadata.project_name = config.metadata.project_name || form.name
    const payload = {
      name: form.name,
      description: form.description,
      cloud_provider: form.cloud_provider,
      region: form.region,
      zone: form.zone,
      config,
    }
    if (editingId.value) {
      await updateIaCStack(editingId.value, payload)
      ElMessage.success('方案已更新')
    } else {
      await createIaCStack(payload)
      ElMessage.success('方案创建成功')
    }
    switchTab('stacks')
    fetchStacks()
  } catch (e) {
    // 拦截器已提示
  } finally {
    saving.value = false
  }
}

function openExecute(row) {
  currentStack.value = row
  executeForm.action = 'init'
  executeForm.secrets = {}
  executeVisible.value = true
}

async function submitExecute() {
  if (!currentStack.value) return
  executing.value = true
  try {
    const data = await executeIaCStack(currentStack.value.id, {
      action: executeForm.action,
      secrets: executeForm.secrets,
    })
    executeVisible.value = false
    ElMessage.success(data.message || '执行完成')
    fetchStacks()
    if (detailVisible.value && detail.value && detail.value.id === currentStack.value.id) {
      openDetail(detail.value)
    }
  } catch (e) {
    // 拦截器已提示
  } finally {
    executing.value = false
  }
}

async function syncCmdb(row) {
  try {
    const data = await syncIaCStackCmdb(row.id)
    ElMessage.success(data.message || 'CMDB 同步完成')
    fetchStacks()
  } catch (e) {
    // 拦截器已提示
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除方案「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteIaCStack(row.id)
    ElMessage.success('方案已删除')
    fetchStacks()
  } catch (e) {
    // 取消或错误
  }
}

function viewExecution(row) {
  logDetail.value = row
  logVisible.value = true
}

onMounted(() => {
  loadPermissions()
  fetchCatalog()
  fetchStacks()
})
</script>

<style scoped>
.iac-hero {
  background: linear-gradient(135deg, #fbfdff 0%, #f7faff 52%, #f9fbfd 100%);
  border-color: rgba(36, 91, 219, 0.09);
  display: flex;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0;
}

.iac-hero-desc {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.45;
}

.iac-page-shell :deep(.release-hero-title-row) {
  display: flex;
  align-items: center;
  gap: 12px;
}

.iac-page-shell :deep(.release-hero-title-inline) {
  flex-wrap: wrap;
}

.iac-page-shell :deep(.hero h2) {
  margin: 0;
  font-size: 23px;
  color: #0f172a;
}

.iac-header-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.25);
}

.iac-top-stats {
  margin-top: 16px;
}

.iac-summary-card {
  padding: 14px 18px;
}

.iac-summary-card.success-tone .stat-value {
  color: #16a34a;
}

.iac-summary-card.danger-tone .stat-value {
  color: #dc2626;
}

.iac-summary-card.info-tone .stat-value {
  color: #2563eb;
}

.iac-main-tabs {
  margin-top: 16px;
}

.iac-stack-card,
.iac-form-card {
  margin-top: 12px;
}

.iac-stack-toolbar {
  margin-top: 8px;
}

.iac-stack-table :deep(.el-table__cell) {
  font-size: 13px;
}

.section-divider-label {
  font-weight: 600;
  color: #1e293b;
}

.iac-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.iac-detail-head {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.iac-detail-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.iac-detail-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  color: #64748b;
  font-size: 13px;
}

.iac-detail-desc {
  margin-bottom: 16px;
}

.iac-detail-section-title {
  font-weight: 600;
  margin: 16px 0 8px;
  color: #1e293b;
}

.iac-detail-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.iac-file-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}

.iac-log-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.iac-log-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.iac-log-command {
  font-family: 'JetBrains Mono', 'Cascadia Code', Consolas, monospace;
  color: #64748b;
  font-size: 12px;
}

.iac-log-block {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', 'Cascadia Code', Consolas, monospace;
  font-size: 12px;
  max-height: 360px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.iac-log-stderr {
  background: #1e1b1b;
  color: #fca5a5;
}

.muted-text {
  color: #94a3b8;
  font-size: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #94a3b8;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
  color: #cbd5e1;
}
</style>
