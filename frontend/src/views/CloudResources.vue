<template>
  <div class="fade-in workbench-page-shell cloudres-page-shell">
    <section class="hero panel cloudres-hero">
      <div class="release-hero-copy">
        <div class="release-hero-title-row release-hero-title-inline">
          <span class="release-header-icon cloudres-header-icon"><el-icon><Service /></el-icon></span>
          <h2>CMDB</h2>
          <p class="subtitle inline-subtitle cloudres-hero-desc">统一管理云账号、云环境与配置项清单，支持腾讯云、华为云、AWS 等多家云厂商。</p>
        </div>
      </div>
    </section>

    <div class="audit-grid cloudres-top-stats">
      <div v-for="card in summaryCards" :key="card.label" class="audit-card audit-card--inline cloudres-summary-card" :class="card.tone">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value">{{ card.value }}</div>
      </div>
    </div>

    <div class="neo-tabs theme-blue cloudres-main-tabs">
      <button v-for="tab in mainTabs" :key="tab.key" class="neo-tab-btn" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        <el-icon style="margin-right:4px;"><component :is="tab.icon" /></el-icon>
        {{ tab.label }}
      </button>
    </div>

    <!-- 云账号 -->
    <div v-if="activeTab === 'credentials'" class="workbench-card cloudres-card">
      <div class="section-toolbar">
        <div class="toolbar-head">
          <span class="toolbar-title">云账号</span>
          <span class="toolbar-desc">配置各云厂商 AK/SK 凭证，测试连通性并触发资源同步。</span>
        </div>
        <div class="workbench-card-actions">
          <el-button class="filter-refresh-btn" @click="fetchCredentials"><el-icon><RefreshRight /></el-icon>刷新</el-button>
          <el-button v-if="canManage" class="filter-refresh-btn" type="primary" @click="openCredForm()"><el-icon><Plus /></el-icon>新增账号</el-button>
        </div>
      </div>
      <el-table :data="credentials" stripe v-loading="credentialsLoading" style="width:100%">
        <el-table-column label="账号名称" min-width="170">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="cloud-provider-icon" :style="{ background: providerColor(row.provider) }"><el-icon><component :is="providerIcon(row.provider)" /></el-icon></span>
              <div>
                <div style="font-weight:600">{{ row.name }}</div>
                <div class="muted-text">{{ row.account_name || row.account_id }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="云厂商" width="110">
          <template #default="{ row }"><el-tag size="small" effect="plain" :color="providerColor(row.provider)" style="border:none;color:#fff;">{{ row.provider_label }}</el-tag></template>
        </el-table-column>
        <el-table-column label="环境" prop="environment_count" width="70" align="center" />
        <el-table-column label="资源" prop="asset_count" width="70" align="center" />
        <el-table-column label="区域" prop="default_region" width="120" />
        <el-table-column label="最近同步" width="150">
          <template #default="{ row }"><span v-if="row.last_sync_at">{{ formatTime(row.last_sync_at) }}</span><span v-else class="muted-text">未同步</span></template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canManage" link type="primary" size="small" @click="openCredForm(row)">编辑</el-button>
            <el-button v-if="canManage" link type="success" size="small" @click="testConnection(row)">测试连接</el-button>
            <el-button v-if="canSync" link type="warning" size="small" @click="syncAccount(row)">同步</el-button>
            <el-button v-if="canManage" link type="danger" size="small" @click="confirmDeleteCred(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 云环境 -->
    <div v-else-if="activeTab === 'environments'" class="workbench-card cloudres-card">
      <div class="section-toolbar">
        <div class="toolbar-head">
          <span class="toolbar-title">云环境</span>
          <span class="toolbar-desc">按区域划分的云环境，可触发资源发现与同步到 CMDB。</span>
        </div>
        <div class="workbench-card-actions">
          <el-button class="filter-refresh-btn" @click="fetchEnvironments"><el-icon><RefreshRight /></el-icon>刷新</el-button>
        </div>
      </div>
      <el-table :data="environments" stripe v-loading="environmentsLoading" style="width:100%">
        <el-table-column label="环境名称" min-width="170">
          <template #default="{ row }"><span style="font-weight:600">{{ row.name }}</span></template>
        </el-table-column>
        <el-table-column label="账号" prop="credential_name" width="120" />
        <el-table-column label="云厂商" width="100">
          <template #default="{ row }"><el-tag size="small" effect="plain">{{ row.provider_label }}</el-tag></template>
        </el-table-column>
        <el-table-column label="类型" prop="environment_type_label" width="90" />
        <el-table-column label="区域" prop="region" width="120" />
        <el-table-column label="同步状态" width="100">
          <template #default="{ row }"><el-tag :type="syncStatusTagType(row.sync_status)" size="small">{{ row.sync_status_label }}</el-tag></template>
        </el-table-column>
        <el-table-column label="资源" prop="asset_count" width="70" align="center" />
        <el-table-column label="月成本" width="100" align="right">
          <template #default="{ row }">￥{{ Number(row.monthly_cost || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canSync" link type="primary" size="small" @click="syncEnvironment(row)">资源发现</el-button>
            <el-button v-if="canSync" link type="warning" size="small" @click="syncEnvironmentCmdb(row)">同步 CMDB</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 清单 (云资源 + CMDB 配置项合并) -->
    <div v-else-if="activeTab === 'inventory'" class="workbench-card cloudres-card">
      <div class="cloudres-inventory-tabs">
        <button class="cloudres-inv-tab" :class="{ active: inventoryTab === 'assets' }" @click="switchInventoryTab('assets')">
          <el-icon style="margin-right:4px;"><Collection /></el-icon>云资源
        </button>
        <button class="cloudres-inv-tab" :class="{ active: inventoryTab === 'items' }" @click="switchInventoryTab('items')">
          <el-icon style="margin-right:4px;"><Coin /></el-icon>CMDB 配置项
        </button>
      </div>

      <template v-if="inventoryTab === 'assets'">
        <div class="section-toolbar cloudres-section-toolbar">
          <div class="toolbar-head">
            <span class="toolbar-title">云资源清单</span>
            <span class="toolbar-desc">各云厂商发现的云资源实例，含自动风险评级。</span>
          </div>
          <div class="workbench-card-actions">
            <el-button class="filter-refresh-btn" @click="fetchAssets"><el-icon><RefreshRight /></el-icon>刷新</el-button>
          </div>
        </div>
        <div class="workbench-toolbar workbench-toolbar--history cloudres-toolbar">
          <el-input v-model="assetKeyword" clearable placeholder="搜索名称 / IP / 规格" style="width: 220px" />
          <el-select v-model="assetProvider" clearable placeholder="云厂商" style="width: 130px">
            <el-option v-for="(meta, key) in catalog" :key="key" :label="meta.label" :value="key" />
          </el-select>
          <el-tag v-if="assetProvider" closable size="large" @close="assetProvider = null">{{ catalog[assetProvider]?.label }}</el-tag>
        </div>
        <el-table :data="filteredAssets" stripe v-loading="assetsLoading" style="width:100%">
          <el-table-column label="资源名称" min-width="180">
            <template #default="{ row }">
              <div style="display:flex;align-items:center;gap:8px;">
                <span class="cloud-provider-icon" :style="{ background: providerColor(row.provider) }"><el-icon><component :is="providerIcon(row.provider)" /></el-icon></span>
                <span style="font-weight:600">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="110">
            <template #default="{ row }"><el-tag size="small" type="info" effect="plain">{{ row.resource_type_label }}</el-tag></template>
          </el-table-column>
          <el-table-column label="区域" prop="region" width="110" />
          <el-table-column label="内网 IP" prop="private_ip" width="120" />
          <el-table-column label="规格" prop="spec" min-width="120">
            <template #default="{ row }"><span v-if="row.spec">{{ row.spec }}</span><span v-else class="muted-text">—</span></template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }"><el-tag :type="statusTagType(row.status)" size="small">{{ row.status_label }}</el-tag></template>
          </el-table-column>
          <el-table-column label="月成本" width="100" align="right">
            <template #default="{ row }">￥{{ Number(row.monthly_cost || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="风险" width="110">
            <template #default="{ row }">
              <el-tag v-if="row.risk_level && row.risk_level !== 'normal'" :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level_label }}</el-tag>
              <span v-else class="muted-text">正常</span>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <template v-else>
        <div class="section-toolbar cloudres-section-toolbar">
          <div class="toolbar-head">
            <span class="toolbar-title">CMDB 配置项</span>
            <span class="toolbar-desc">CMDB 中的基础设施配置项，含 IaC / 多云同步的资源。</span>
          </div>
          <div class="workbench-card-actions">
            <el-button class="filter-refresh-btn" @click="fetchCmdbItems"><el-icon><RefreshRight /></el-icon>刷新</el-button>
          </div>
        </div>
        <div class="workbench-toolbar workbench-toolbar--history cloudres-toolbar">
          <el-input v-model="cmdbKeyword" clearable placeholder="搜索名称 / 负责人 / 业务线" style="width: 220px" />
          <el-select v-model="cmdbStatus" clearable placeholder="状态" style="width: 120px">
            <el-option label="使用中" value="active" />
            <el-option label="闲置" value="idle" />
            <el-option label="已下线" value="offline" />
          </el-select>
        </div>
        <el-table :data="filteredCmdbItems" stripe v-loading="cmdbItemsLoading" style="width:100%">
          <el-table-column label="配置项" min-width="180">
            <template #default="{ row }">
              <div style="display:flex;align-items:center;gap:8px;cursor:pointer;" @click="openCmdbDetail(row)">
                <span class="cmdb-ci-icon" :style="{ background: row.ci_type_color || '#9c27b0' }"><el-icon><component :is="ciIcon(row.ci_type_icon)" /></el-icon></span>
                <span style="font-weight:600">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="120">
            <template #default="{ row }"><el-tag size="small" effect="plain" :color="row.ci_type_color" style="border:none;color:#fff;">{{ row.ci_type_name }}</el-tag></template>
          </el-table-column>
          <el-table-column label="环境" width="80">
            <template #default="{ row }"><el-tag size="small" type="info" effect="plain">{{ row.environment_display }}</el-tag></template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }"><el-tag :type="cmdbStatusTagType(row.status)" size="small">{{ row.status_display }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="business_line" label="业务线" width="100" />
          <el-table-column prop="admin_user" label="负责人" width="100" />
          <el-table-column label="关系" prop="relation_count" width="70" align="center" />
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openCmdbDetail(row)">详情</el-button>
              <el-button v-if="canManageCmdb" link type="primary" size="small" @click="openCmdbEdit(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </div>

    <!-- 拓扑视图 -->
    <div v-else-if="activeTab === 'topology'" class="workbench-card cloudres-card cloudres-topology-card">
      <CmdbTopologyPanel :ci-types="ciTypeOptions" :resource-tree="resourceTree" :can-manage="canManageCmdb" />
    </div>

    <!-- 资源申请 -->
    <div v-else-if="activeTab === 'requests'" class="workbench-card cloudres-card">
      <CmdbRequestsPanel :resource-tree="resourceTree" />
    </div>

    <!-- 成本总览 -->
    <div v-else-if="activeTab === 'costs'" class="workbench-card cloudres-card">
      <div class="section-toolbar">
        <div class="toolbar-head">
          <span class="toolbar-title">成本总览</span>
          <span class="toolbar-desc">各云厂商月度成本与资源分布。</span>
        </div>
      </div>
      <div v-loading="overviewLoading">
        <div class="cloudres-section-title">按云厂商</div>
        <el-table :data="overview.provider_summary || []" stripe style="width:100%">
          <el-table-column label="云厂商" min-width="140">
            <template #default="{ row }">
              <div style="display:flex;align-items:center;gap:8px;">
                <span class="cloud-provider-icon" :style="{ background: providerColor(row.provider) }"><el-icon><component :is="providerIcon(row.provider)" /></el-icon></span>
                <span style="font-weight:600">{{ row.provider_label }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="账号" prop="credentials" width="80" align="center" />
          <el-table-column label="环境" prop="environments" width="80" align="center" />
          <el-table-column label="资源" prop="assets" width="80" align="center" />
          <el-table-column label="月成本" width="120" align="right">
            <template #default="{ row }">￥{{ Number(row.monthly_cost || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="风险" prop="risk_count" width="80" align="center" />
        </el-table>
      </div>
    </div>

    <!-- 账号表单弹窗 -->
    <el-dialog v-model="credFormVisible" :title="credForm.id ? '编辑云账号' : '新增云账号'" width="600px" append-to-body>
      <el-form :model="credForm" label-width="120px">
        <el-form-item label="云厂商" required>
          <el-select v-model="credForm.provider" style="width:100%">
            <el-option v-for="(meta, key) in catalog" :key="key" :label="meta.label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号名称" required><el-input v-model="credForm.name" placeholder="例如 prod-aliyun" /></el-form-item>
        <el-form-item label="AccessKey ID"><el-input v-model="credForm.access_key_id" /></el-form-item>
        <el-form-item label="AccessKey Secret"><el-input v-model="credForm.access_key_secret" type="password" show-password :placeholder="credForm.id ? '留空保持不变' : ''" /></el-form-item>
        <el-form-item v-if="credForm.provider === 'huawei'" label="Project ID"><el-input v-model="credForm.project_id" placeholder="华为云项目 ID" /></el-form-item>
        <el-form-item label="默认区域"><el-input v-model="credForm.default_region" :placeholder="defaultRegionHint" /></el-form-item>
        <el-form-item label="Demo 模式"><el-switch v-model="credForm.demo_mode" active-text="启用" inactive-text="停用" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="credForm.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="credFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingCred" @click="saveCredential">保存</el-button>
      </template>
    </el-dialog>

    <!-- CMDB 配置项详情弹窗 -->
    <el-dialog v-model="cmdbDetailVisible" title="配置项详情" width="620px" top="6vh" append-to-body>
      <div v-if="cmdbDetail">
        <div class="cmdb-detail-head">
          <div class="cmdb-detail-title">
            <span class="cmdb-ci-icon" :style="{ background: cmdbDetail.ci_type_color || '#9c27b0' }"><el-icon><component :is="ciIcon(cmdbDetail.ci_type_icon)" /></el-icon></span>
            <span>{{ cmdbDetail.name }}</span>
          </div>
          <el-tag :type="cmdbStatusTagType(cmdbDetail.status)" size="small">{{ cmdbDetail.status_display }}</el-tag>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">{{ cmdbDetail.ci_type_name }}</el-descriptions-item>
          <el-descriptions-item label="环境">{{ cmdbDetail.environment_display }}</el-descriptions-item>
          <el-descriptions-item label="业务线">{{ cmdbDetail.business_line || '—' }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ cmdbDetail.admin_user || '—' }}</el-descriptions-item>
          <el-descriptions-item label="关系数">{{ cmdbDetail.relation_count }}</el-descriptions-item>
          <el-descriptions-item label="更新于">{{ formatTime(cmdbDetail.updated_at) }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="Object.keys(cmdbDetail.attributes || {}).length" class="cloudres-section-title">扩展属性</div>
        <el-descriptions v-if="Object.keys(cmdbDetail.attributes || {}).length" :column="2" border>
          <el-descriptions-item v-for="(value, key) in cmdbDetail.attributes" :key="key" :label="key">{{ formatAttr(value) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- CMDB 配置项编辑弹窗 -->
    <el-dialog v-model="cmdbEditVisible" title="编辑配置项" width="520px" append-to-body>
      <el-form v-if="cmdbEditForm" :model="cmdbEditForm" label-width="100px">
        <el-form-item label="名称"><el-input v-model="cmdbEditForm.name" /></el-form-item>
        <el-form-item label="业务线"><el-input v-model="cmdbEditForm.business_line" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="cmdbEditForm.admin_user" /></el-form-item>
        <el-form-item label="环境">
          <el-select v-model="cmdbEditForm.environment" style="width:100%">
            <el-option label="生产" value="prod" /><el-option label="测试" value="test" /><el-option label="开发" value="dev" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="cmdbEditForm.status" style="width:100%">
            <el-option label="使用中" value="active" /><el-option label="闲置" value="idle" /><el-option label="已下线" value="offline" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cmdbEditVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingCmdb" @click="saveCmdbEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Service, RefreshRight, Plus, Box, Collection, Coin, Share, Tickets, TrendCharts, Connection } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import CmdbTopologyPanel from '@/components/cmdb/CmdbTopologyPanel.vue'
import CmdbRequestsPanel from '@/components/cmdb/CmdbRequestsPanel.vue'
import {
  getCloudCredentials, createCloudCredential, updateCloudCredential, deleteCloudCredential,
  testCloudConnection, syncCloudAll,
  getCloudEnvironments, syncCloudEnvironment, syncCloudCmdb,
  getCloudAssets, getCloudOverview, getCloudCatalog,
} from '@/api/modules/multicloud'
import { getConfigItems, updateConfigItem, getCITypes, getResourceNodeTree, getCmdbDashboard } from '@/api/modules/cmdb'

const activeTab = ref('credentials')
const credentials = ref([])
const credentialsLoading = ref(false)
const environments = ref([])
const environmentsLoading = ref(false)
const assets = ref([])
const assetsLoading = ref(false)
const overview = ref({})
const overviewLoading = ref(false)
const catalog = ref({})
const canManage = ref(false)
const canSync = ref(false)
const canManageCmdb = ref(false)

const assetKeyword = ref('')
const assetProvider = ref(null)

const cmdbItems = ref([])
const cmdbItemsLoading = ref(false)
const cmdbKeyword = ref('')
const cmdbStatus = ref(null)
const cmdbDetailVisible = ref(false)
const cmdbDetail = ref(null)
const cmdbEditVisible = ref(false)
const cmdbEditForm = ref(null)
const savingCmdb = ref(false)
const ciTypeOptions = ref([])
const resourceTree = ref([])

const credFormVisible = ref(false)
const credForm = reactive({ id: null, provider: 'aliyun', name: '', access_key_id: '', access_key_secret: '', project_id: '', default_region: '', demo_mode: false, description: '' })
const savingCred = ref(false)

const mainTabs = [
  { key: 'credentials', label: '云账号', icon: Service },
  { key: 'environments', label: '云环境', icon: Box },
  { key: 'inventory', label: '清单', icon: Collection },
  { key: 'topology', label: '拓扑视图', icon: Share },
  { key: 'requests', label: '资源申请', icon: Tickets },
  { key: 'costs', label: '成本总览', icon: TrendCharts },
]

const inventoryTab = ref('assets')

const ciIconMap = {
  monitor: Connection, connection: Connection, lock: Coin, position: Coin,
  coin: Coin, dataanalysis: TrendCharts, switch: Service, link: Share,
  folderopened: Box, box: Box, component: Coin, 'data-analysis': TrendCharts,
  'folder-opened': Box,
}

const summaryCards = computed(() => [
  { label: '云账号', value: overview.value.stats?.credential_count ?? credentials.value.length, tone: '' },
  { label: '云环境', value: overview.value.stats?.environment_count ?? environments.value.length, tone: 'info-tone' },
  { label: '云资源', value: overview.value.stats?.asset_count ?? assets.value.length, tone: 'success-tone' },
  { label: '月成本(万)', value: formatWan(overview.value.stats?.monthly_cost), tone: 'danger-tone' },
])

const defaultRegionHint = computed(() => {
  const meta = catalog.value[credForm.provider]
  return meta ? `默认 ${meta.default_region}` : ''
})

const filteredAssets = computed(() => {
  const keyword = assetKeyword.value.trim().toLowerCase()
  return assets.value.filter((a) => {
    if (assetProvider.value && a.provider !== assetProvider.value) return false
    if (keyword) {
      const hay = [a.name, a.private_ip, a.public_ip, a.spec, a.region].filter(Boolean).join(' ').toLowerCase()
      if (!hay.includes(keyword)) return false
    }
    return true
  })
})

const filteredCmdbItems = computed(() => {
  const keyword = cmdbKeyword.value.trim().toLowerCase()
  return cmdbItems.value.filter((item) => {
    if (cmdbStatus.value && item.status !== cmdbStatus.value) return false
    if (keyword) {
      const hay = [item.name, item.admin_user, item.business_line, item.ci_type_name].filter(Boolean).join(' ').toLowerCase()
      if (!hay.includes(keyword)) return false
    }
    return true
  })
})

function formatWan(value) {
  return (Number(value || 0) / 10000).toFixed(1)
}

function providerColor(provider) {
  return { aliyun: '#ff6a00', tencent: '#006eff', huawei: '#cf0a2c', aws: '#ff9900', baidu: '#2932e1' }[provider] || '#64748b'
}

function providerIcon(provider) {
  return { aliyun: Connection, tencent: Coin, huawei: Box, aws: Service, baidu: Connection }[provider] || Service
}

function ciIcon(name) {
  return ciIconMap[String(name || '').toLowerCase()] || Box
}

function statusTagType(status) {
  if (status === 'running') return 'success'
  return 'info'
}

function syncStatusTagType(status) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'running') return 'warning'
  return 'info'
}

function riskTagType(level) {
  if (level === 'critical') return 'danger'
  if (level === 'warning') return 'warning'
  return 'info'
}

function cmdbStatusTagType(status) {
  if (status === 'active') return 'success'
  if (status === 'idle') return 'warning'
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
  if (key === 'inventory') {
    fetchAssets()
    fetchCmdbItems()
  }
  if (key === 'environments') fetchEnvironments()
  if (key === 'costs') fetchOverview()
}

function switchInventoryTab(key) {
  inventoryTab.value = key
  if (key === 'assets') fetchAssets()
  else fetchCmdbItems()
}

function loadPermissions() {
  const authStore = useAuthStore()
  canManage.value = authStore.hasAnyPermission(['ops.multicloud.manage'])
  canSync.value = authStore.hasAnyPermission(['ops.multicloud.sync'])
  canManageCmdb.value = authStore.hasAnyPermission(['cmdb.ci.manage'])
}

async function fetchCatalog() {
  try {
    const data = await getCloudCatalog()
    catalog.value = data.providers || data
  } catch (e) { /* 拦截器已提示 */ }
}

async function fetchCredentials() {
  credentialsLoading.value = true
  try { credentials.value = await getCloudCredentials() } catch (e) { /* 拦截器已提示 */ } finally { credentialsLoading.value = false }
}

async function fetchEnvironments() {
  environmentsLoading.value = true
  try { environments.value = await getCloudEnvironments() } catch (e) { /* 拦截器已提示 */ } finally { environmentsLoading.value = false }
}

async function fetchAssets() {
  assetsLoading.value = true
  try {
    const data = await getCloudAssets()
    assets.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) { /* 拦截器已提示 */ } finally { assetsLoading.value = false }
}

async function fetchOverview() {
  overviewLoading.value = true
  try { overview.value = await getCloudOverview() } catch (e) { /* 拦截器已提示 */ } finally { overviewLoading.value = false }
}

async function fetchCmdbItems() {
  cmdbItemsLoading.value = true
  try {
    const response = await getConfigItems()
    cmdbItems.value = Array.isArray(response) ? response : (response.results || [])
  } catch (e) { /* 拦截器已提示 */ } finally { cmdbItemsLoading.value = false }
}

async function fetchCmdbMeta() {
  try {
    const [types, tree, dash] = await Promise.all([getCITypes(), getResourceNodeTree(), getCmdbDashboard()])
    ciTypeOptions.value = types
    resourceTree.value = tree
    if (!overview.value.stats) overview.value.stats = { ci_total: dash.ci_total, ci_active: dash.ci_active, relation_count: dash.relation_count }
  } catch (e) { /* 拦截器已提示 */ }
}

function openCredForm(row) {
  if (!row) {
    Object.assign(credForm, { id: null, provider: 'aliyun', name: '', access_key_id: '', access_key_secret: '', project_id: '', default_region: '', demo_mode: false, description: '' })
  } else {
    Object.assign(credForm, { id: row.id, provider: row.provider, name: row.name, access_key_id: row.access_key_id, access_key_secret: '', project_id: row.project_id, default_region: row.default_region, demo_mode: row.demo_mode, description: row.description })
  }
  credFormVisible.value = true
}

async function saveCredential() {
  if (!credForm.name) { ElMessage.warning('请填写账号名称'); return }
  savingCred.value = true
  try {
    const payload = { provider: credForm.provider, name: credForm.name, access_key_id: credForm.access_key_id, default_region: credForm.default_region, project_id: credForm.project_id, demo_mode: credForm.demo_mode, description: credForm.description }
    if (credForm.access_key_secret) payload.access_key_secret = credForm.access_key_secret
    if (credForm.id) { await updateCloudCredential(credForm.id, payload); ElMessage.success('云账号已更新') } else { await createCloudCredential(payload); ElMessage.success('云账号已创建') }
    credFormVisible.value = false
    fetchCredentials(); fetchOverview()
  } catch (e) { /* 拦截器已提示 */ } finally { savingCred.value = false }
}

async function testConnection(row) {
  try {
    const result = await testCloudConnection(row.id)
    if (result.success) ElMessage.success(result.message || '连接正常')
    else ElMessage.warning(result.message || '连接失败')
  } catch (e) { /* 拦截器已提示 */ }
}

async function syncAccount(row) {
  try {
    ElMessage.info(`正在同步 ${row.name} 的云环境资源...`)
    await syncCloudAll(row.id)
    ElMessage.success('同步完成')
    fetchCredentials(); fetchOverview()
  } catch (e) { /* 拦截器已提示 */ }
}

async function syncEnvironment(row) {
  try {
    ElMessage.info(`正在发现 ${row.name} 的云资源...`)
    await syncCloudEnvironment(row.id)
    ElMessage.success('资源发现完成')
    fetchEnvironments(); fetchAssets()
  } catch (e) { /* 拦截器已提示 */ }
}

async function syncEnvironmentCmdb(row) {
  try {
    await syncCloudCmdb(row.id)
    ElMessage.success('已同步到 CMDB')
  } catch (e) { /* 拦截器已提示 */ }
}

async function confirmDeleteCred(row) {
  try {
    await ElMessageBox.confirm(`确定删除云账号「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteCloudCredential(row.id)
    ElMessage.success('云账号已删除')
    fetchCredentials(); fetchOverview()
  } catch (e) { /* 取消或错误 */ }
}

function openCmdbDetail(row) {
  cmdbDetail.value = row
  cmdbDetailVisible.value = true
}

function openCmdbEdit(row) {
  cmdbEditForm.value = { id: row.id, name: row.name, business_line: row.business_line, admin_user: row.admin_user, environment: row.environment, status: row.status }
  cmdbEditVisible.value = true
}

async function saveCmdbEdit() {
  if (!cmdbEditForm.value) return
  savingCmdb.value = true
  try {
    await updateConfigItem(cmdbEditForm.value.id, cmdbEditForm.value)
    ElMessage.success('配置项已更新')
    cmdbEditVisible.value = false
    fetchCmdbItems()
  } catch (e) { /* 拦截器已提示 */ } finally { savingCmdb.value = false }
}

onMounted(() => {
  loadPermissions()
  fetchCatalog()
  fetchCredentials()
  fetchEnvironments()
  fetchAssets()
  fetchOverview()
  fetchCmdbItems()
  fetchCmdbMeta()
})
</script>

<style scoped>
.cloudres-hero {
  background: linear-gradient(135deg, #fbfdff 0%, #f7faff 52%, #f9fbfd 100%);
  border-color: rgba(36, 91, 219, 0.09);
  display: flex;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0;
}

.cloudres-hero-desc {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.45;
}

.cloudres-page-shell :deep(.release-hero-title-row) {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cloudres-page-shell :deep(.hero h2) {
  margin: 0;
  font-size: 23px;
  color: #0f172a;
}

.cloudres-header-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  box-shadow: 0 10px 20px rgba(14, 165, 233, 0.25);
}

.cloudres-top-stats {
  margin-top: 16px;
}

.cloudres-summary-card {
  padding: 14px 18px;
}

.cloudres-summary-card.success-tone .stat-value { color: #16a34a; }
.cloudres-summary-card.danger-tone .stat-value { color: #dc2626; }
.cloudres-summary-card.info-tone .stat-value { color: #2563eb; }

.cloudres-main-tabs {
  margin-top: 16px;
}

.cloudres-inventory-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid #eef1f5;
  padding-bottom: 10px;
  margin-bottom: 8px;
}

.cloudres-inv-tab {
  border: none;
  background: transparent;
  padding: 8px 18px;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  font-size: 14px;
  color: #64748b;
  transition: all 0.2s;
}

.cloudres-inv-tab:hover {
  background: #f1f5f9;
  color: #334155;
}

.cloudres-inv-tab.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}

.cloudres-section-toolbar {
  padding: 0;
}

.cloudres-card {
  margin-top: 12px;
}

.cloudres-topology-card {
  min-height: 560px;
}

.cloudres-toolbar {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cloud-provider-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  flex-shrink: 0;
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

.cloudres-section-title {
  font-weight: 600;
  margin: 16px 0 8px;
  color: #1e293b;
}

.muted-text {
  color: #94a3b8;
  font-size: 12px;
}
</style>
