<template>
  <div class="slave-monitor">
    <!-- 页面头部 -->
    <el-card class="header-card">
      <div class="monitor-header">
        <div class="header-left">
          <h2>{{ slave?.name }} - 服务器监控</h2>
          <el-tag :type="slave?.isActive ? 'success' : 'danger'">
            {{ slave?.isActive ? '在线' : '离线' }}
          </el-tag>
        </div>
        <div class="header-actions">
          <el-button-group>
            <el-button
              :type="timeRange === '1h' ? 'primary' : ''"
              @click="handleTimeRangeChange('1h')"
            >
              1小时
            </el-button>
            <el-button
              :type="timeRange === '6h' ? 'primary' : ''"
              @click="handleTimeRangeChange('6h')"
            >
              6小时
            </el-button>
            <el-button
              :type="timeRange === '24h' ? 'primary' : ''"
              @click="handleTimeRangeChange('24h')"
            >
              24小时
            </el-button>
          </el-button-group>
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
    </el-card>

    <!-- 实时指标卡片 -->
    <div class="metrics-grid">
      <el-card class="metric-card">
        <div class="metric-content">
          <div class="metric-icon cpu">
            <el-icon><CPU /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-name">CPU使用率</div>
            <div class="metric-value">{{ formatPercent(currentMetrics.cpuUsage) }}</div>
          </div>
        </div>
        <el-progress
          :percentage="currentMetrics.cpuUsage"
          :status="getProgressStatus(currentMetrics.cpuUsage)"
        />
      </el-card>

      <el-card class="metric-card">
        <div class="metric-content">
          <div class="metric-icon memory">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-name">内存使用率</div>
            <div class="metric-value">{{ formatPercent(currentMetrics.memoryUsage) }}</div>
          </div>
        </div>
        <el-progress
          :percentage="currentMetrics.memoryUsage"
          :status="getProgressStatus(currentMetrics.memoryUsage)"
        />
      </el-card>

      <el-card class="metric-card">
        <div class="metric-content">
          <div class="metric-icon devices">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-name">设备连接数</div>
            <div class="metric-value">{{ currentMetrics.deviceCount }}</div>
          </div>
        </div>
        <div class="device-stats">
          <el-tag type="success">在线: {{ currentMetrics.onlineDevices }}</el-tag>
          <el-tag type="warning">占用: {{ currentMetrics.occupiedDevices }}</el-tag>
          <el-tag type="danger">离线: {{ currentMetrics.offlineDevices }}</el-tag>
        </div>
      </el-card>

      <el-card class="metric-card">
        <div class="metric-content">
          <div class="metric-icon network">
            <el-icon><DataLine /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-name">网络流量</div>
            <div class="metric-value">{{ formatBytes(currentMetrics.networkTraffic) }}/s</div>
          </div>
        </div>
        <div class="network-stats">
          <div>上行: {{ formatBytes(currentMetrics.uploadTraffic) }}/s</div>
          <div>下行: {{ formatBytes(currentMetrics.downloadTraffic) }}/s</div>
        </div>
      </el-card>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- CPU使用率趋势图 -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>CPU使用率趋势</h3>
            <el-tooltip content="每5秒更新一次数据">
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="cpuChartOption" autoresize />
        </div>
      </el-card>

      <!-- 内存使用率趋势图 -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>内存使用率趋势</h3>
            <el-tooltip content="每5秒更新一次数据">
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="memoryChartOption" autoresize />
        </div>
      </el-card>

      <!-- 设备状态分布图 -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>设备状态分布</h3>
            <el-tooltip content="实时更新设备状态">
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="deviceChartOption" autoresize />
        </div>
      </el-card>

      <!-- 网络流量趋势图 -->
      <el-card class="chart-card">
        <template #header>
          <div class="chart-header">
            <h3>网络流量趋势</h3>
            <el-tooltip content="每5秒更新一次数据">
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
        </template>
        <div class="chart-container">
          <v-chart class="chart" :option="networkChartOption" autoresize />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'
import {
  Refresh,
  Back,
  Monitor,
  Connection,
  DataLine,
  InfoFilled,
  Cpu
} from '@element-plus/icons-vue'
import { useWebSocket } from '@/composables/useWebSocket'
import type { WebSocketInstance } from '@/composables/useWebSocket'
import { formatDateTimeString, formatBytes, formatPercentage } from '@/utils/format'
import { getSlaveById, getSlaveMetrics } from '@/api/slaves'
import type { Slave, SlaveMetric } from '@/api/slaves'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent
])

const route = useRoute()
const router = useRouter()

// WebSocket 连接
const { isConnected, subscribe, unsubscribe } = useWebSocket({
  url: `ws://${window.location.host}/api/ws/slaves/${route.params.id}`
})

// 从服务器信息
const slave = ref<Slave | null>(null)
const loading = ref(false)
const timeRange = ref<'1h' | '6h' | '24h'>('1h')

// 当前指标数据
const currentMetrics = reactive<{
  cpuUsage: number
  memoryUsage: number
  deviceCount: number
  onlineDevices: number
  occupiedDevices: number
  offlineDevices: number
  networkTraffic: number
  uploadTraffic: number
  downloadTraffic: number
}>({
  cpuUsage: 0,
  memoryUsage: 0,
  deviceCount: 0,
  onlineDevices: 0,
  occupiedDevices: 0,
  offlineDevices: 0,
  networkTraffic: 0,
  uploadTraffic: 0,
  downloadTraffic: 0
})

// 历史数据
const metricsHistory = reactive<{
  timestamps: string[]
  cpuUsage: number[]
  memoryUsage: number[]
  networkTraffic: number[]
}>({
  timestamps: [],
  cpuUsage: [],
  memoryUsage: [],
  networkTraffic: []
})

// 获取从服务器信息
const fetchSlaveInfo = async () => {
  try {
    loading.value = true
    const data = await getSlaveById(route.params.id as string)
    slave.value = data
  } catch (error) {
    console.error('Fetch slave info error:', error)
    ElMessage.error('获取从服务器信息失败')
  } finally {
    loading.value = false
  }
}

// 获取监控数据
const fetchMetrics = async () => {
  try {
    loading.value = true
    const data = await getSlaveMetrics(route.params.id as string, timeRange.value)
    
    // 更新历史数据
    metricsHistory.timestamps = data.map(m => m.timestamp)
    metricsHistory.cpuUsage = data.map(m => m.cpuUsage)
    metricsHistory.memoryUsage = data.map(m => m.memoryUsage)
    metricsHistory.networkTraffic = data.map(m => m.networkTraffic)
    
    // 更新当前指标
    if (data.length > 0) {
      const latest = data[data.length - 1]
      currentMetrics.cpuUsage = latest.cpuUsage
      currentMetrics.memoryUsage = latest.memoryUsage
      currentMetrics.deviceCount = latest.deviceCount
      currentMetrics.onlineDevices = latest.onlineDevices
      currentMetrics.networkTraffic = latest.networkTraffic
    }
  } catch (error) {
    console.error('Fetch metrics error:', error)
    ElMessage.error('获取监控数据失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const handleRefresh = () => {
  fetchSlaveInfo()
  fetchMetrics()
}

// 返回列表
const handleBack = () => {
  router.push('/slaves')
}

// 时间范围变化
const handleTimeRangeChange = () => {
  fetchMetrics()
}

// 格式化百分比
const formatPercent = (value: number) => {
  return `${Math.round(value)}%`
}

onMounted(() => {
  fetchSlaveInfo()
  fetchMetrics()

  // 订阅从服务器状态更新
  subscribe('slave_status', (data) => {
    slave.value = {
      ...slave.value,
      ...data
    } as Slave
  })

  // 订阅监控数据更新
  subscribe('slave_metrics', (data: SlaveMetric) => {
    currentMetrics.cpuUsage = data.cpuUsage
    currentMetrics.memoryUsage = data.memoryUsage
    currentMetrics.deviceCount = data.deviceCount
    currentMetrics.onlineDevices = data.onlineDevices
    currentMetrics.networkTraffic = data.networkTraffic
  })
})

onUnmounted(() => {
  unsubscribe('slave_status')
  unsubscribe('slave_metrics')
})

// 获取进度条状态
const getProgressStatus = (value: number) => {
  if (value >= 90) return 'exception'
  if (value >= 70) return 'warning'
  return 'success'
}

// CPU使用率图表配置
const cpuChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params: any) => {
      const time = params[0].axisValue
      const value = params[0].value
      return `${time}<br/>CPU使用率: ${formatPercent(value)}`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: metricsHistory.timestamps
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 100,
    axisLabel: {
      formatter: '{value}%'
    }
  },
  series: [
    {
      name: 'CPU使用率',
      type: 'line',
      smooth: true,
      data: metricsHistory.cpuUsage,
      areaStyle: {
        opacity: 0.1
      },
      lineStyle: {
        width: 2
      }
    }
  ]
}))

// 内存使用率图表配置
const memoryChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params: any) => {
      const time = params[0].axisValue
      const value = params[0].value
      return `${time}<br/>内存使用率: ${formatPercent(value)}`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: metricsHistory.timestamps
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 100,
    axisLabel: {
      formatter: '{value}%'
    }
  },
  series: [
    {
      name: '内存使用率',
      type: 'line',
      smooth: true,
      data: metricsHistory.memoryUsage,
      areaStyle: {
        opacity: 0.1
      },
      lineStyle: {
        width: 2
      }
    }
  ]
}))

// 设备状态分布图表配置
const deviceChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'horizontal',
    bottom: 'bottom'
  },
  series: [
    {
      name: '设备状态',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '16',
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: [
        { 
          value: currentMetrics.onlineDevices,
          name: '在线',
          itemStyle: { color: '#67C23A' }
        },
        {
          value: currentMetrics.occupiedDevices,
          name: '占用',
          itemStyle: { color: '#E6A23C' }
        },
        {
          value: currentMetrics.offlineDevices,
          name: '离线',
          itemStyle: { color: '#F56C6C' }
        }
      ]
    }
  ]
}))

// 网络流量图表配置
const networkChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params: any) => {
      const time = params[0].axisValue
      const value = params[0].value
      return `${time}<br/>网络流量: ${formatBytes(value)}/s`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: metricsHistory.timestamps
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (value: number) => formatBytes(value)
    }
  },
  series: [
    {
      name: '网络流量',
      type: 'line',
      smooth: true,
      data: metricsHistory.networkTraffic,
      areaStyle: {
        opacity: 0.1
      },
      lineStyle: {
        width: 2
      }
    }
  ]
}))
</script>

<style scoped>
.slave-monitor {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-card {
  margin-bottom: 0;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
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
}

.metric-card {
  margin-bottom: 0;
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  font-size: 24px;
}

.cpu {
  background-color: rgba(64, 158, 255, 0.1);
  color: #409EFF;
}

.memory {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67C23A;
}

.devices {
  background-color: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

.network {
  background-color: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.metric-info {
  flex: 1;
}

.metric-name {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
}

.device-stats,
.network-stats {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-card {
  margin-bottom: 0;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.chart-container {
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}
</style> 