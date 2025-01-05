<template>
  <div class="monitor-dashboard">
    <a-row :gutter="16">
      <!-- 系统状态卡片 -->
      <a-col :span="24">
        <a-card class="status-card" :loading="loading">
          <template #title>系统状态</template>
          <a-row :gutter="16">
            <a-col :span="6">
              <a-statistic
                title="CPU使用率"
                :value="metrics.cpu_usage"
                :precision="2"
                suffix="%"
                :value-style="getValueStyle(metrics.cpu_usage, 80)"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="内存使用率"
                :value="metrics.memory_usage"
                :precision="2"
                suffix="%"
                :value-style="getValueStyle(metrics.memory_usage, 85)"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="活动设备"
                :value="metrics.active_devices"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="系统状态"
                :value="health.status"
                :value-style="getHealthStyle(health.status)"
              />
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <!-- 告警面板 -->
      <a-col :span="12">
        <a-card class="alert-card" :loading="loading">
          <template #title>活动告警</template>
          <a-list
            :data-source="activeAlerts"
            :pagination="{ pageSize: 5 }"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-tag :color="getAlertColor(item.severity)">
                  {{ item.severity }}
                </a-tag>
                <span>{{ item.description }}</span>
                <span>{{ formatTime(item.timestamp) }}</span>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>

      <!-- 故障面板 -->
      <a-col :span="12">
        <a-card class="fault-card" :loading="loading">
          <template #title>活动故障</template>
          <a-list
            :data-source="activeFaults"
            :pagination="{ pageSize: 5 }"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-tag :color="getFaultColor(item.severity)">
                  {{ item.severity }}
                </a-tag>
                <span>{{ item.description }}</span>
                <span>{{ formatTime(item.timestamp) }}</span>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>

      <!-- 设备统计图表 -->
      <a-col :span="24">
        <a-card class="stats-card" :loading="loading">
          <template #title>设备使用统计</template>
          <a-row :gutter="16">
            <a-col :span="12">
              <v-chart :option="deviceUsageOption" />
            </a-col>
            <a-col :span="12">
              <v-chart :option="deviceStatusOption" />
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
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
import * as echarts from 'echarts/core'
import {
  Refresh,
  Monitor,
  Connection,
  DataLine,
  InfoFilled,
  Cpu
} from '@element-plus/icons-vue'
import { useWebSocket } from '@/composables/useWebSocket'
import type { WebSocketInstance } from '@/composables/useWebSocket'
import { formatDateTimeString, formatBytes, formatPercentage } from '@/utils/format'
import { getMonitorData, getMonitorStats, getMonitorSummary } from '@/api/monitor'
import type { MonitorData, MonitorStats, MonitorSummary } from '@/api/monitor'

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

// 监控数据
const monitorData = ref<MonitorData[]>([])
const monitorStats = ref<Record<string, MonitorStats>>({})
const monitorSummary = ref<MonitorSummary | null>(null)
const loading = ref(false)
const timeRange = ref<'1h' | '6h' | '24h'>('1h')

// 图表实例引用
const cpuChartRef = ref<HTMLElement | null>(null)
const memoryChartRef = ref<HTMLElement | null>(null)
const diskChartRef = ref<HTMLElement | null>(null)
const networkChartRef = ref<HTMLElement | null>(null)

// 图表实例
let cpuChart: echarts.ECharts | null = null
let memoryChart: echarts.ECharts | null = null
let diskChart: echarts.ECharts | null = null
let networkChart: echarts.ECharts | null = null

// 初始化图表
const initCharts = () => {
  if (cpuChartRef.value) {
    cpuChart = echarts.init(cpuChartRef.value)
  }
  if (memoryChartRef.value) {
    memoryChart = echarts.init(memoryChartRef.value)
  }
  if (diskChartRef.value) {
    diskChart = echarts.init(diskChartRef.value)
  }
  if (networkChartRef.value) {
    networkChart = echarts.init(networkChartRef.value)
  }
}

// 更新图表
const updateCharts = () => {
  if (!monitorData.value.length) return

  // 更新CPU图表
  if (cpuChart) {
    const cpuData = monitorData.value.filter(d => d.type === 'cpu')
    cpuChart.setOption({
      xAxis: {
        type: 'time',
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [{
        name: 'CPU使用率',
        type: 'line',
        smooth: true,
        data: cpuData.map(d => [d.timestamp, d.value])
      }]
    })
  }

  // 更新内存图表
  if (memoryChart) {
    const memoryData = monitorData.value.filter(d => d.type === 'memory')
    memoryChart.setOption({
      xAxis: {
        type: 'time',
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [{
        name: '内存使用率',
        type: 'line',
        smooth: true,
        data: memoryData.map(d => [d.timestamp, d.value])
      }]
    })
  }

  // 更新磁盘图表
  if (diskChart) {
    const diskData = monitorData.value.filter(d => d.type === 'disk')
    diskChart.setOption({
      xAxis: {
        type: 'time',
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [{
        name: '磁盘使用率',
        type: 'line',
        smooth: true,
        data: diskData.map(d => [d.timestamp, d.value])
      }]
    })
  }

  // 更新网络图表
  if (networkChart) {
    const networkData = monitorData.value.filter(d => d.type === 'network')
    networkChart.setOption({
      xAxis: {
        type: 'time',
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => formatBytes(value)
        }
      },
      series: [{
        name: '网络流量',
        type: 'line',
        smooth: true,
        data: networkData.map(d => [d.timestamp, d.value])
      }]
    })
  }
}

// 获取监控数据
const fetchMonitorData = async () => {
  try {
    loading.value = true
    const [data, stats, summary] = await Promise.all([
      getMonitorData({
        startTime: getStartTime(),
        endTime: new Date().toISOString(),
        interval: getInterval()
      }),
      getMonitorStats('cpu'),
      getMonitorSummary()
    ])
    monitorData.value = data
    monitorStats.value = {
      cpu: await getMonitorStats('cpu'),
      memory: await getMonitorStats('memory'),
      disk: await getMonitorStats('disk'),
      network: await getMonitorStats('network')
    }
    monitorSummary.value = summary
    updateCharts()
  } catch (error) {
    console.error('Fetch monitor data error:', error)
    ElMessage.error('获取监控数据失败')
  } finally {
    loading.value = false
  }
}

// 获取开始时间
const getStartTime = () => {
  const now = new Date()
  switch (timeRange.value) {
    case '1h':
      return new Date(now.getTime() - 3600000).toISOString()
    case '6h':
      return new Date(now.getTime() - 21600000).toISOString()
    case '24h':
      return new Date(now.getTime() - 86400000).toISOString()
    default:
      return new Date(now.getTime() - 3600000).toISOString()
  }
}

// 获取数据间隔
const getInterval = () => {
  switch (timeRange.value) {
    case '1h':
      return 60
    case '6h':
      return 300
    case '24h':
      return 900
    default:
      return 60
  }
}

// 刷新数据
const handleRefresh = () => {
  fetchMonitorData()
}

// 时间范围变化
const handleTimeRangeChange = () => {
  fetchMonitorData()
}

// WebSocket 连接
const { isConnected, subscribe, unsubscribe } = useWebSocket({
  url: `ws://${window.location.host}/api/ws/monitor`
})

onMounted(() => {
  initCharts()
  fetchMonitorData()

  // 订阅监控数据更新
  subscribe('monitor_data', (data: MonitorData) => {
    monitorData.value.push(data)
    if (monitorData.value.length > 100) {
      monitorData.value.shift()
    }
    updateCharts()
  })

  // 订阅监控统计更新
  subscribe('monitor_stats', (data: Record<string, MonitorStats>) => {
    monitorStats.value = data
  })

  // 订阅监控摘要更新
  subscribe('monitor_summary', (data: MonitorSummary) => {
    monitorSummary.value = data
  })

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  unsubscribe('monitor_data')
  unsubscribe('monitor_stats')
  unsubscribe('monitor_summary')
  window.removeEventListener('resize', handleResize)

  // 销毁图表实例
  cpuChart?.dispose()
  memoryChart?.dispose()
  diskChart?.dispose()
  networkChart?.dispose()
})

// 处理窗口大小变化
const handleResize = () => {
  cpuChart?.resize()
  memoryChart?.resize()
  diskChart?.resize()
  networkChart?.resize()
}

// 样式计算
const getValueStyle = (value: number, threshold: number) => ({
  color: value > threshold ? '#cf1322' : '#3f8600'
});

const getHealthStyle = (status: string) => ({
  color: status === 'healthy' ? '#3f8600' : '#cf1322'
});

const getAlertColor = (severity: string) => {
  const colors = {
    critical: 'red',
    warning: 'orange',
    info: 'blue'
  };
  return colors[severity] || 'blue';
};

const getFaultColor = (severity: string) => {
  const colors = {
    critical: 'red',
    major: 'orange',
    minor: 'yellow'
  };
  return colors[severity] || 'blue';
};

// 图表配置
const deviceUsageOption = ref<EChartsOption>({
  title: { text: '设备使用趋势' },
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'time' },
  yAxis: { type: 'value' },
  series: [{
    name: '活动设备数',
    type: 'line',
    data: []
  }]
});

const deviceStatusOption = ref<EChartsOption>({
  title: { text: '设备状态分布' },
  tooltip: { trigger: 'item' },
  series: [{
    name: '设备状态',
    type: 'pie',
    radius: '50%',
    data: []
  }]
});

return {
  loading,
  metrics,
  health,
  activeAlerts,
  activeFaults,
  deviceUsageOption,
  deviceStatusOption,
  getValueStyle,
  getHealthStyle,
  getAlertColor,
  getFaultColor,
  formatTime: formatDateTime,
  formatPercentage
};
</script>

<style lang="less" scoped>
.monitor-dashboard {
  padding: 24px;

  .ant-card {
    margin-bottom: 24px;
  }

  .status-card {
    .ant-statistic {
      text-align: center;
    }
  }

  .alert-card,
  .fault-card {
    height: 400px;
    overflow-y: auto;
  }

  .stats-card {
    .echarts {
      height: 400px;
    }
  }
}
</style> 