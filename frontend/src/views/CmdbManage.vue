<template>
  <div class="fade-in workbench-page-shell cmdb-page-shell">
    <section class="hero panel cmdb-hero">
      <div class="release-hero-copy">
        <div class="release-hero-title-row release-hero-title-inline">
          <span class="release-header-icon cmdb-header-icon"><el-icon><Coin /></el-icon></span>
          <h2>云资源管理</h2>
          <p class="subtitle inline-subtitle cmdb-hero-desc">统一维护云上配置项、资源拓扑与资源申请，支持与 IaC 方案双向关联。</p>
        </div>
      </div>
    </section>

    <div class="audit-grid cmdb-top-stats">
      <div v-for="card in summaryCards" :key="card.label" class="audit-card audit-card--inline cmdb-summary-card" :class="card.tone">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value">{{ card.value }}</div>
      </div>
    </div>

    <div class="neo-tabs theme-blue cmdb-main-tabs">
      <button v-for="tab in mainTabs" :key="tab.key" class="neo-tab-btn" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        <el-icon style="margin-right:4px;"><component :is="tab.icon" /></el-icon>
        {{ tab.label }}
      </button>
    </div>

    <!-- 资源清单 -->
    <div v-if="activeTab === 'items'" class="workbench-card cmdb-items-card">
      <div class="section-toolbar">
        <div class="toolbar-head">
          <span class="toolbar-title">配置项清单</span>
          <span class="toolbar-desc">所有基础设施配置项，包括 IaC 同步生成的云资源。</span>
        </div>
        <div class="workbench-card-actions">
          <el-button class="filter-refresh-btn" @click="fetchItems">
            <el-icon><RefreshRight /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <div class="workbench-toolbar workbench-toolbar--history cmdb-items-toolbar">
        <div class="workbench-toolbar-left">
          <el-input v-model="searchKeyword" clearable placeholder="搜索名称 / 负责人 / 业务线" style="width: 260px" />
          <el-select v-model="filterType" clearable placeholder="CI 类型" style="width: 150px">
            <el-option v-for="t in ciTypeOptions" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <el-select v-model="filterStatus" clearable placeholder="状态" style="width: 130px">
            <el-option label="使用中" value="active" />
            <el-option label="闲置" value="idle" />
            <el-option label="已下线" value="offline" />
          </el-select>
          <el-select v-model="filterEnv" clearable placeholder="环境" style="width: 130px">
            <el-option label="生产" value="prod" />
            <el-option label="测试" value="test" />
            <el-option label="开发" value="dev" />
          </el-select>
        </div>
      </div>

      <el-table :data="filteredItems" stripe v-loading="loading" style="width:100%" class="cmdb-items-table">
        <el-table-column label="配置项" min-width="180">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px;cursor:pointer;" @click="openDetail(row)">
              <span class="cmdb-ci-icon" :style="{ background: row.ci_type_color || '#9c27b0' }">
                <el-icon><component :is="iconComponent(row.ci_type_icon)" /></el-icon>
              </span>
              <span style="font-weight:600">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :color="row.ci_type_color" style="border:none;color:#fff;">
              {{ row.ci_type_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="环境" width="80">
          <template #default="{ row }">
            <el-tag size="small" type="info" effect="plain">{{ row.environment_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="business_line" label="业务线" width="100" />
        <el-table-column prop="admin_user" label="负责人" width="100" />
        <el-table-column label="关系" width="70" align="center">
          <template #default="{ row }">{{ row.relation_count }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="canManage" link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !filteredItems.length" class="empty-state">
        <div class="empty-icon">◇</div>
        <div class="empty-text">暂无配置项。可通过 IaC 方案「同步 CMDB」或手动创建资源。</div>
      </div>
    </div>

    <!-- 拓扑视图 -->
    <div v-if="activeTab === 'topology'" class="workbench-card cmdb-topology-card">
      <CmdbTopologyPanel :ci-types="ciTypeOptions" :resource-tree="resourceTree" :can-manage="canManage" />
    </div>

    <!-- 资源申请 -->
    <div v-if="activeTab === 'requests'" class="workbench-card cmdb-requests-card">
      <CmdbRequestsPanel :resource-tree="resourceTree" />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="配置项详情" width="620px" top="6vh" append-to-body>
      <div v-if="detail" v-loading="detailLoading">
        <div class="cmdb-detail-head">
          <div class="cmdb-detail-title">
            <span class="cmdb-ci-icon" :style="{ background: detail.ci_type_color || '#9c27b0' }">
              <el-icon><component :is="iconComponent(detail.ci_type_icon)" /></el-icon>
            </span>
            <span>{{ detail.name }}</span>
          </div>
          <el-tag :type="statusTagType(detail.status)" size="small">{{ detail.status_display }}</el-tag>
        </div>
        <el-descriptions :column="2" border class="cmdb-detail-desc">
          <el-descriptions-item label="类型">{{ detail.ci_type_name }}</el-descriptions-item>
          <el-descriptions-item label="环境">{{ detail.environment_display }}</el-descriptions-item>
          <el-descriptions-item label="业务线">{{ detail.business_line || '—' }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ detail.admin_user || '—' }}</el-descriptions-item>
          <el-descriptions-item label="关系数">{{ detail.relation_count }}</el-descriptions-item>
          <el-descriptions-item label="更新于">{{ formatTime(detail.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="Object.keys(detail.attributes || {}).length" class="cmdb-detail-section-title">扩展属性</div>
        <el-descriptions v-if="Object.keys(detail.attributes || {}).length" :column="2" border>
          <el-descriptions-item
            v-for="(value, key) in detail.attributes"
            :key="key"
            :label="key"
          >{{ formatAttr(value) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑配置项" width="520px" append-to-body>
      <el-form v-if="editForm" :model="editForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="业务线">
          <el-input v-model="editForm.business_line" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="editForm.admin_user" />
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="editForm.environment" style="width:100%">
            <el-option label="生产" value="prod" />
            <el-option label="测试" value="test" />
            <el-option label="开发" value="dev" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width:100%">
            <el-option label="使用中" value="active" />
            <el-option label="闲置" value="idle" />
            <el-option label="已下线" value="offline" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Coin,
  RefreshRight,
  Collection,
  Share,
  Tickets,
  Monitor,
  Connection,
  Lock,
  Position,
  Coin as CoinIcon,
  DataAnalysis,
  Switch,
  Link,
  FolderOpened,
  Box,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import CmdbTopologyPanel from '@/components/cmdb/CmdbTopologyPanel.vue'
import CmdbRequestsPanel from '@/components/cmdb/CmdbRequestsPanel.vue'
import {
  getConfigItems,
  updateConfigItem,
  getCmdbDashboard,
  getCITypes,
  getResourceNodeTree,
} from '@/api/modules/cmdb'

const activeTab = ref('items')
const loading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
const items = ref([])
const detail = ref(null)
const detailVisible = ref(false)
const editVisible = ref(false)
const editForm = ref(null)
const searchKeyword = ref('')
const filterType = ref(null)
const filterStatus = ref(null)
const filterEnv = ref(null)
const ciTypeOptions = ref([])
const resourceTree = ref([])
const dashboard = ref({})
const canManage = ref(false)

const mainTabs = [
  { key: 'items', label: '资源清单', icon: Collection },
  { key: 'topology', label: '拓扑视图', icon: Share },
  { key: 'requests', label: '资源申请', icon: Tickets },
]

const iconMap = {
  monitor: Monitor,
  connection: Connection,
  lock: Lock,
  position: Position,
  coin: CoinIcon,
  dataanalysis: DataAnalysis,
  switch: Switch,
  link: Link,
  folderopened: FolderOpened,
  box: Box,
  component: CoinIcon,
  'data-analysis': DataAnalysis,
  'folder-opened': FolderOpened,
  'switch-button': Switch,
  box: Box,
}

const summaryCards = computed(() => [
  { label: '配置项总数', value: dashboard.value.ci_total ?? items.value.length, tone: '' },
  { label: '使用中', value: dashboard.value.ci_active ?? items.value.filter(i => i.status === 'active').length, tone: 'success-tone' },
  { label: '关系数', value: dashboard.value.relation_count ?? 0, tone: 'info-tone' },
  { label: '待审批申请', value: dashboard.value.pending_requests ?? 0, tone: 'danger-tone' },
])

const filteredItems = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return items.value.filter((item) => {
    if (filterType.value && item.ci_type !== filterType.value && item.ci_type_id !== filterType.value) return false
    if (filterStatus.value && item.status !== filterStatus.value) return false
    if (filterEnv.value && item.environment !== filterEnv.value) return false
    if (keyword) {
      const haystack = [item.name, item.admin_user, item.business_line, item.ci_type_name].filter(Boolean).join(' ').toLowerCase()
      if (!haystack.includes(keyword)) return false
    }
    return true
  })
})

function iconComponent(name) {
  const key = String(name || '').toLowerCase()
  return iconMap[key] || Box
}

function statusTagType(status) {
  if (status === 'active') return 'success'
  if (status === 'idle') return 'warning'
  if (status === 'offline') return 'info'
  return 'info'
}

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatAttr(value) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function switchTab(key) {
  activeTab.value = key
  if (key === 'topology') {
    // 由拓扑组件自行加载
  }
}

function loadPermissions() {
  const authStore = useAuthStore()
  canManage.value = authStore.hasAnyPermission(['cmdb.ci.manage'])
}

async function fetchDashboard() {
  try {
    dashboard.value = await getCmdbDashboard()
  } catch (e) {
    // 拦截器已提示
  }
}

async function fetchItems() {
  loading.value = true
  try {
    const response = await getConfigItems()
    items.value = Array.isArray(response) ? response : (response.results || [])
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

async function fetchMeta() {
  try {
    const [types, tree] = await Promise.all([getCITypes(), getResourceNodeTree()])
    ciTypeOptions.value = types
    resourceTree.value = tree
  } catch (e) {
    // 拦截器已提示
  }
}

function openDetail(row) {
  detail.value = row
  detailVisible.value = true
}

function openEdit(row) {
  editForm.value = {
    id: row.id,
    name: row.name,
    business_line: row.business_line,
    admin_user: row.admin_user,
    environment: row.environment,
    status: row.status,
  }
  editVisible.value = true
}

async function saveEdit() {
  if (!editForm.value) return
  saving.value = true
  try {
    await updateConfigItem(editForm.value.id, editForm.value)
    ElMessage.success('配置项已更新')
    editVisible.value = false
    fetchItems()
  } catch (e) {
    // 拦截器已提示
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadPermissions()
  fetchDashboard()
  fetchItems()
  fetchMeta()
})
</script>

<style scoped>
.cmdb-hero {
  background: linear-gradient(135deg, #fbfdff 0%, #f7faff 52%, #f9fbfd 100%);
  border-color: rgba(36, 91, 219, 0.09);
  display: flex;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0;
}

.cmdb-hero-desc {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.45;
}

.cmdb-page-shell :deep(.release-hero-title-row) {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cmdb-page-shell :deep(.hero h2) {
  margin: 0;
  font-size: 23px;
  color: #0f172a;
}

.cmdb-header-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.25);
}

.cmdb-top-stats {
  margin-top: 16px;
}

.cmdb-summary-card {
  padding: 14px 18px;
}

.cmdb-summary-card.success-tone .stat-value {
  color: #16a34a;
}

.cmdb-summary-card.danger-tone .stat-value {
  color: #dc2626;
}

.cmdb-summary-card.info-tone .stat-value {
  color: #2563eb;
}

.cmdb-main-tabs {
  margin-top: 16px;
}

.cmdb-items-card,
.cmdb-topology-card,
.cmdb-requests-card {
  margin-top: 12px;
}

.cmdb-items-toolbar {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cmdb-ci-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  flex-shrink: 0;
}

.cmdb-detail-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.cmdb-detail-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.cmdb-detail-desc {
  margin-bottom: 12px;
}

.cmdb-detail-section-title {
  font-weight: 600;
  margin: 16px 0 8px;
  color: #1e293b;
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
