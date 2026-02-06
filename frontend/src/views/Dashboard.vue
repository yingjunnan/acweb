<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="page-title">系统仪表盘</h1>
      <div class="refresh-info">
        <span class="last-update">最后更新: {{ lastUpdateTime }}</span>
        <a-button size="small" @click="fetchSystemInfo" :loading="loading">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </div>
    </div>
    
    <a-spin :spinning="loading && isFirstLoad">
      <a-row :gutter="[16, 16]">
        <!-- 基本信息 -->
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card title="主机信息" :bordered="false">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="主机名">
                {{ systemInfo.hostname }}
              </a-descriptions-item>
              <a-descriptions-item label="IP地址">
                {{ systemInfo.ip_address }}
              </a-descriptions-item>
              <a-descriptions-item label="系统">
                {{ systemInfo.platform }}
              </a-descriptions-item>
              <a-descriptions-item label="架构">
                {{ systemInfo.architecture }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
        
        <!-- 运行时间 -->
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card title="运行时间" :bordered="false">
            <div class="stat-value">{{ uptime }}</div>
            <div class="stat-label">开机时间</div>
            <a-divider />
            <div class="stat-small">{{ bootTime }}</div>
          </a-card>
        </a-col>
        
        <!-- CPU -->
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card title="CPU" :bordered="false" class="progress-card">
            <div class="progress-wrapper">
              <a-progress
                type="circle"
                :percent="systemInfo.cpu?.percent || 0"
                :width="90"
                :stroke-color="getProgressColor(systemInfo.cpu?.percent || 0)"
              />
            </div>
            <div class="stat-label">{{ systemInfo.cpu?.count || 0 }} 核心</div>
          </a-card>
        </a-col>
        
        <!-- 内存 -->
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card title="内存" :bordered="false" class="progress-card">
            <div class="progress-wrapper">
              <a-progress
                type="circle"
                :percent="systemInfo.memory?.percent || 0"
                :width="90"
                :stroke-color="getProgressColor(systemInfo.memory?.percent || 0)"
              />
            </div>
            <div class="stat-label">
              {{ formatBytes(systemInfo.memory?.used || 0) }} / 
              {{ formatBytes(systemInfo.memory?.total || 0) }}
            </div>
          </a-card>
        </a-col>
        
        <!-- 磁盘 -->
        <a-col :xs="24" :md="12">
          <a-card title="磁盘使用" :bordered="false">
            <a-progress
              :percent="systemInfo.disk?.percent || 0"
              :stroke-color="getProgressColor(systemInfo.disk?.percent || 0)"
            />
            <a-descriptions :column="2" size="small" style="margin-top: 16px">
              <a-descriptions-item label="总容量">
                {{ formatBytes(systemInfo.disk?.total || 0) }}
              </a-descriptions-item>
              <a-descriptions-item label="已使用">
                {{ formatBytes(systemInfo.disk?.used || 0) }}
              </a-descriptions-item>
              <a-descriptions-item label="可用">
                {{ formatBytes(systemInfo.disk?.free || 0) }}
              </a-descriptions-item>
              <a-descriptions-item label="使用率">
                {{ (systemInfo.disk?.percent || 0).toFixed(1) }}%
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
        
        <!-- 网络 -->
        <a-col :xs="24" :md="12">
          <a-card title="网络流量" :bordered="false">
            <a-row :gutter="16">
              <a-col :span="12">
                <div class="network-stat">
                  <ArrowUpOutlined class="network-icon upload" />
                  <div class="network-value">{{ formatBytes(systemInfo.network?.bytes_sent || 0) }}</div>
                  <div class="network-label">上传</div>
                </div>
              </a-col>
              <a-col :span="12">
                <div class="network-stat">
                  <ArrowDownOutlined class="network-icon download" />
                  <div class="network-value">{{ formatBytes(systemInfo.network?.bytes_recv || 0) }}</div>
                  <div class="network-label">下载</div>
                </div>
              </a-col>
            </a-row>
            <a-divider />
            <a-descriptions :column="2" size="small">
              <a-descriptions-item label="发送包">
                {{ formatNumber(systemInfo.network?.packets_sent || 0) }}
              </a-descriptions-item>
              <a-descriptions-item label="接收包">
                {{ formatNumber(systemInfo.network?.packets_recv || 0) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ArrowUpOutlined, ArrowDownOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { useConfigStore } from '../stores/config'
import api from '../api'

const configStore = useConfigStore()
const systemInfo = ref({})
const loading = ref(true)
const isFirstLoad = ref(true)
const lastUpdateTime = ref('')
let refreshTimer = null

const uptime = computed(() => {
  const seconds = systemInfo.value.uptime_seconds || 0
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) {
    return `${days}天 ${hours}小时 ${minutes}分钟`
  } else if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  } else {
    return `${minutes}分钟`
  }
})

const bootTime = computed(() => {
  if (!systemInfo.value.boot_time) return ''
  const date = new Date(systemInfo.value.boot_time)
  return date.toLocaleString('zh-CN')
})

const fetchSystemInfo = async () => {
  try {
    // 只在首次加载时显示 loading
    if (isFirstLoad.value) {
      loading.value = true
    }
    const response = await api.get('/api/v1/system/info')
    systemInfo.value = response.data
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
  } catch (error) {
    console.error('Failed to fetch system info:', error)
  } finally {
    if (isFirstLoad.value) {
      loading.value = false
      isFirstLoad.value = false
    }
  }
}

const startAutoRefresh = () => {
  // 清除旧的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  
  // 根据配置设置刷新间隔
  const interval = (configStore.config.refresh_interval || 3) * 1000
  refreshTimer = setInterval(fetchSystemInfo, interval)
}

// 监听配置变化，动态调整刷新间隔
watch(() => configStore.config.refresh_interval, () => {
  startAutoRefresh()
})

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

const formatNumber = (num) => {
  return num.toLocaleString('zh-CN')
}

const getProgressColor = (percent) => {
  if (percent < 60) return '#52c41a'
  if (percent < 80) return '#faad14'
  return '#f5222d'
}

onMounted(async () => {
  await configStore.loadConfig()
  await fetchSystemInfo()
  startAutoRefresh()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.refresh-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.last-update {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

:deep(.ant-card) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

:deep(.ant-card:hover) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

:deep(.ant-card-head) {
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
  color: #262626;
}

:deep(.ant-card-body) {
  padding: 20px;
}

.progress-card :deep(.ant-card-body) {
  padding: 30px 20px;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.progress-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
  margin: 16px 0;
  letter-spacing: -1px;
}

.stat-label {
  text-align: center;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 8px;
  font-size: 13px;
}

.stat-small {
  text-align: center;
  color: rgba(0, 0, 0, 0.65);
  font-size: 12px;
}

:deep(.ant-progress-circle) {
  display: block;
  margin: 0 auto;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.65);
}

:deep(.ant-descriptions-item-content) {
  color: rgba(0, 0, 0, 0.85);
  font-weight: 500;
}

.network-stat {
  text-align: center;
  padding: 16px 0;
}

.network-icon {
  font-size: 36px;
  margin-bottom: 12px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.network-icon.upload {
  color: #52c41a;
}

.network-icon.download {
  color: #1890ff;
}

.network-value {
  font-size: 22px;
  font-weight: 700;
  margin: 8px 0;
  color: #262626;
}

.network-label {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

:deep(.ant-progress-line) {
  margin-bottom: 8px;
}

:deep(.ant-progress-text) {
  font-weight: 600;
}
</style>
