<template>
  <div class="device-monitor">
    <!-- 基本信息卡片 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <h3>{{ device?.name }}</h3>
            <el-tag :type="getStatusType(device?.status)">
              {{ getStatusName(device?.status) }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button type="primary" @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="handleBack">
              <el-icon><Back /></el-icon>
              返回
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 实时监控数据 -->
      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-label">连接状态</div>
          <div class="metric-value">
            <el-tag :type="realtimeMetrics?.isConnected ? 'success' : 'danger'">
              {{ realtimeMetrics?.isConnected ? '已连接' : '未连接' }}
            </el-tag>
          </div>
        </div>
        <div class="metric-item">
          <div class="metric-label">使用时长</div>
          <div class="metric-value">
            {{ formatDuration(realtimeMetrics?.usageDuration || 0) }}
          </div>
        </div>
        <div class="metric-item">
          <div class="metric-label">带宽使用</div>
          <div class="metric-value">
            {{ formatBitrate(realtimeMetrics?.bandwidthUsage || 0) }}
          </div>
        </div>
        <div class="metric-item">
          <div class="metric-label">错误次数</div>
          <div class="metric-value error-count">
            {{ realtimeMetrics?.errorCount || 0 }}
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 历史数据图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <h3>历史数据</h3>
          <div class="header-actions">
            <el-radio-group v-model="timeRange" @change="handleTimeRangeChange">
              <el-radio-button label="1h">1小时</el-radio-button>
              <el-radio-button label="6h">6小时</el-radio-button>
              <el-radio-button label="24h">24小时</el-radio-button>
              <el-radio-button label="7d">7天</el-radio-button>
              <el-radio-button label="30d">30天</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      
      <div class="charts">
        <!-- 带宽使用图表 -->
        <div class="chart-container">
          <div ref="bandwidthChartRef" class="chart"></div>
        </div>
        
        <!-- 错误次数图表 -->
        <div class="chart-container">
          <div ref="errorChartRef" class="chart"></div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Back } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useWebSocket } from '@/composables/useWebSocket'
import { formatDuration, formatBitrate, formatDateTimeString, formatBytes, formatPercentage } from '@/utils/format'
import {
  getDeviceById,
  getDeviceMetrics,
  getDeviceMetricsRealtime
} from '@/api/devices'
import type { Device, DeviceMetrics } from '@/types/device'

const route = useRoute()
const router = useRouter()
const { subscribe, unsubscribe } = useWebSocket()

// 设备信息
const device = ref<Device | null>(null)
const realtimeMetrics = ref<DeviceMetrics | null>(null)
const loading = ref(false)

// 图表相关
const bandwidthChartRef = ref<HTMLElement | null>(null)
const errorChartRef = ref<HTMLElement | null>(null)
const bandwidthChart = ref<echarts.ECharts | null>(null)
const errorChart = ref<echarts.ECharts | null>(null)
const timeRange = ref<string>('1h')

// 获取设备信息
const fetchDeviceInfo = async () => {
  try {
    loading.value = true
    const deviceId = Number(route.params.id)
    const data = await getDeviceById(deviceId)
    device.value = data
  } catch (error) {
    console.error('Fetch device info error:', error)
    ElMessage.error('获取设备信息失败')
  } finally {
    loading.value = false
  }
}

// 获取实时监控数据
const fetchRealtimeMetrics = async () => {
  try {
    const deviceId = Number(route.params.id)
    const data = await getDeviceMetricsRealtime(deviceId)
    realtimeMetrics.value = data
  } catch (error) {
    console.error('Fetch realtime metrics error:', error)
  }
}

// 获取历史监控数据
const fetchHistoryMetrics = async () => {
  try {
    loading.value = true
    const deviceId = Number(route.params.id)
    const now = new Date()
    const end = now.toISOString()
    const start = new Date(now.getTime() - getTimeRangeMilliseconds()).toISOString()
    
    const params = {
      deviceId,
      startTime: start,
      endTime: end,
      interval: getTimeInterval()
    }
    
    const { items } = await getDeviceMetrics(params)
    updateCharts(items)
  } catch (error) {
    console.error('Fetch history metrics error:', error)
    ElMessage.error('获取历史数据失败')
  } finally {
    loading.value = false
  }
}

// 获取时间范围的毫秒数
const getTimeRangeMilliseconds = () => {
  const ranges: Record<string, number> = {
    '1h': 3600 * 1000,
    '6h': 6 * 3600 * 1000,
    '24h': 24 * 3600 * 1000,
    '7d': 7 * 24 * 3600 * 1000,
    '30d': 30 * 24 * 3600 * 1000
  }
  return ranges[timeRange.value]
}

// 获取时间间隔
const getTimeInterval = () => {
  const intervals: Record<string, string> = {
    '1h': '1m',
    '6h': '5m',
    '24h': '15m',
    '7d': '1h',
    '30d': '6h'
  }
  return intervals[timeRange.value]
}

// 初始化图表
const initCharts = () => {
  if (bandwidthChartRef.value) {
    bandwidthChart.value = echarts.init(bandwidthChartRef.value)
  }
  if (errorChartRef.value) {
    errorChart.value = echarts.init(errorChartRef.value)
  }
}

// 更新图表数据
const updateCharts = (metrics: DeviceMetrics[]) => {
  const timestamps = metrics.map(m => new Date(m.timestamp).toLocaleString())
  const bandwidthData = metrics.map(m => m.bandwidthUsage)
  const errorData = metrics.map(m => m.errorCount)
  
  // 带宽使用图表
  bandwidthChart.value?.setOption({
    title: {
      text: '带宽使用',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>${formatBitrate(data.value)}`
      }
    },
    xAxis: {
      type: 'category',
      data: timestamps
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => formatBitrate(value)
      }
    },
    series: [
      {
        type: 'line',
        data: bandwidthData,
        smooth: true,
        areaStyle: {}
      }
    ]
  })
  
  // 错误次数图表
  errorChart.value?.setOption({
    title: {
      text: '错误次数',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: timestamps
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        type: 'bar',
        data: errorData
      }
    ]
  })
}

// 刷新
const handleRefresh = () => {
  fetchDeviceInfo()
  fetchRealtimeMetrics()
  fetchHistoryMetrics()
}

// 返回
const handleBack = () => {
  router.back()
}

// 时间范围变化
const handleTimeRangeChange = () => {
  fetchHistoryMetrics()
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  bandwidthChart.value?.resize()
  errorChart.value?.resize()
}

// WebSocket订阅设备状态和指标更新
const subscribeUpdates = () => {
  const deviceId = Number(route.params.id)
  
  // 订阅设备状态更新
  subscribe('device_status', (data) => {
    const updatedDevice = data.device
    if (updatedDevice.id === deviceId) {
      device.value = { ...device.value, ...updatedDevice }
    }
  })
  
  // 订阅设备指标更新
  subscribe('device_metrics', (data) => {
    const metrics = data.metrics
    if (metrics.deviceId === deviceId) {
      realtimeMetrics.value = metrics
    }
  })
}

// 获取状态类型
const getStatusType = (status?: string) => {
  if (!status) return 'info'
  const types: Record<string, string> = {
    online: 'success',
    offline: 'danger',
    occupied: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态名称
const getStatusName = (status?: string) => {
  if (!status) return '-'
  const names: Record<string, string> = {
    online: '在线',
    offline: '离线',
    occupied: '占用'
  }
  return names[status] || status
}

onMounted(() => {
  fetchDeviceInfo()
  fetchRealtimeMetrics()
  initCharts()
  fetchHistoryMetrics()
  subscribeUpdates()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  unsubscribe('device_status')
  unsubscribe('device_metrics')
  window.removeEventListener('resize', handleResize)
  bandwidthChart.value?.dispose()
  errorChart.value?.dispose()
})
</script>

<style scoped>
.device-monitor {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.chart-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.metric-item {
  padding: 20px;
  border-radius: 8px;
  background-color: var(--el-fill-color-light);
}

.metric-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
}

.error-count {
  color: var(--el-color-danger);
}

.charts {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 20px;
}

.chart-container {
  width: 100%;
}

.chart {
  width: 100%;
  height: 300px;
}
</style> 