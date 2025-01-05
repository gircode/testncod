<template>
  <div class="monitor-container">
    <el-row :gutter="20">
      <!-- 系统状态卡片 -->
      <el-col :span="24">
        <el-card class="system-metrics">
          <template #header>
            <div class="card-header">
              <span>系统状态监控</span>
              <el-tag :type="systemHealth ? 'success' : 'danger'">
                {{ systemHealth ? '运行正常' : '系统异常' }}
              </el-tag>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="metric-item">
                <div class="metric-title">CPU使用率</div>
                <el-progress 
                  type="dashboard" 
                  :percentage="systemMetrics.cpu_percent"
                  :color="getColorForMetric(systemMetrics.cpu_percent)">
                </el-progress>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-item">
                <div class="metric-title">内存使用率</div>
                <el-progress 
                  type="dashboard" 
                  :percentage="systemMetrics.memory_percent"
                  :color="getColorForMetric(systemMetrics.memory_percent)">
                </el-progress>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-item">
                <div class="metric-title">磁盘使用率</div>
                <el-progress 
                  type="dashboard" 
                  :percentage="systemMetrics.disk_usage"
                  :color="getColorForMetric(systemMetrics.disk_usage)">
                </el-progress>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-item">
                <div class="metric-title">网络状态</div>
                <div class="network-stats">
                  <p>发送: {{ formatBytes(systemMetrics.network_io?.bytes_sent) }}</p>
                  <p>接收: {{ formatBytes(systemMetrics.network_io?.bytes_recv) }}</p>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 设备列表 -->
      <el-col :span="24" class="mt-4">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>设备状态监控</span>
              <el-button type="primary" @click="refreshDevices">刷新</el-button>
            </div>
          </template>
          <el-table :data="devices" style="width: 100%">
            <el-table-column prop="name" label="设备名称" />
            <el-table-column prop="ip_address" label="IP地址" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_online" label="最后在线时间">
              <template #default="scope">
                {{ formatDateTime(scope.row.last_online) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button 
                  size="small" 
                  @click="showDeviceDetail(scope.row)">
                  详情
                </el-button>
                <el-button 
                  size="small"
                  type="primary" 
                  @click="showPortStatus(scope.row)">
                  端口状态
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备详情对话框 -->
    <el-dialog
      v-model="deviceDetailVisible"
      title="设备详情"
      width="50%">
      <device-detail
        v-if="selectedDevice"
        :device="selectedDevice"
        @update="handleDeviceUpdate"
      />
    </el-dialog>

    <!-- 端口状态对话框 -->
    <el-dialog
      v-model="portStatusVisible"
      title="端口状态"
      width="60%">
      <port-status
        v-if="selectedDevice"
        :device-id="selectedDevice.id"
        @update="handlePortUpdate"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { useStore } from 'vuex'
import DeviceDetail from '@/components/DeviceDetail.vue'
import PortStatus from '@/components/PortStatus.vue'
import { getSystemMetrics, getDevices } from '@/api/monitor'

const store = useStore()
const systemMetrics = ref({})
const devices = ref([])
const deviceDetailVisible = ref(false)
const portStatusVisible = ref(false)
const selectedDevice = ref(null)
const systemHealth = ref(true)

const ws = useWebSocket({
  onMessage: handleWebSocketMessage,
  onError: handleWebSocketError
})

// WebSocket消息处理
function handleWebSocketMessage(message) {
  const data = JSON.parse(message)
  switch (data.type) {
    case 'system_metrics':
      systemMetrics.value = data.data
      break
    case 'device_status':
      updateDeviceStatus(data.device_id, data.status)
      break
    case 'device_error':
      handleDeviceError(data)
      break
  }
}

// 更新设备状态
function updateDeviceStatus(deviceId, status) {
  const device = devices.value.find(d => d.id === deviceId)
  if (device) {
    device.status = status
    device.last_online = new Date().toISOString()
  }
}

// 获取系统指标
async function fetchSystemMetrics() {
  try {
    const response = await getSystemMetrics()
    systemMetrics.value = response.data
    systemHealth.value = true
  } catch (error) {
    console.error('获取系统指标失败:', error)
    systemHealth.value = false
  }
}

// 获取设备列表
async function fetchDevices() {
  try {
    const response = await getDevices()
    devices.value = response.data
  } catch (error) {
    console.error('获取设备列表失败:', error)
    ElMessage.error('获取设备列表失败')
  }
}

// 定时刷新数据
let metricsTimer = null
onMounted(() => {
  fetchSystemMetrics()
  fetchDevices()
  metricsTimer = setInterval(fetchSystemMetrics, 30000)
})

onUnmounted(() => {
  if (metricsTimer) {
    clearInterval(metricsTimer)
  }
  ws.close()
})

// 工具函数
function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

function getColorForMetric(value) {
  if (value >= 90) return '#F56C6C'
  if (value >= 70) return '#E6A23C'
  return '#67C23A'
}

function getStatusType(status) {
  const types = {
    online: 'success',
    offline: 'info',
    error: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    online: '在线',
    offline: '离线',
    error: '异常'
  }
  return texts[status] || status
}
</script>

<style scoped>
.monitor-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-item {
  text-align: center;
  padding: 10px;
}

.metric-title {
  margin-bottom: 15px;
  font-size: 16px;
  color: #606266;
}

.network-stats {
  margin-top: 20px;
}

.mt-4 {
  margin-top: 16px;
}
</style> 