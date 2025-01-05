<template>
  <div class="master-monitor">
    <!-- 系统状态概览 -->
    <a-card class="mb-4">
      <template #title>系统状态</template>
      
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic title="主服务器状态" :value="masterStatus">
            <template #prefix>
              <a-tag :type="masterStatus === 'running' ? 'success' : 'danger'">
                {{ masterStatus === 'running' ? '运行中' : '已停止' }}
              </a-tag>
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="6">
          <a-statistic title="在线从服务器" :value="stats.onlineSlaves" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="在线设备" :value="stats.onlineDevices" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="活跃用户" :value="stats.activeUsers" />
        </a-col>
      </a-row>
    </a-card>

    <!-- 系统日志 -->
    <a-card class="mb-4">
      <template #title>系统日志</template>
      <template #extra>
        <a-space>
          <a-range-picker v-model:value="dateRange" />
          <a-select v-model:value="logLevel" style="width: 120px">
            <a-select-option value="">全部级别</a-select-option>
            <a-select-option value="info">信息</a-select-option>
            <a-select-option value="warning">警告</a-select-option>
            <a-select-option value="error">错误</a-select-option>
            <a-select-option value="debug">调试</a-select-option>
          </a-select>
          <a-select v-model:value="logSource" style="width: 120px">
            <a-select-option value="">全部来源</a-select-option>
            <a-select-option value="master">主服务器</a-select-option>
            <a-select-option value="slave">从服务器</a-select-option>
            <a-select-option value="device">设备</a-select-option>
            <a-select-option value="user">用户</a-select-option>
            <a-select-option value="system">系统</a-select-option>
          </a-select>
          <a-button type="primary" @click="searchLogs">
            搜索
          </a-button>
        </a-space>
      </template>

      <a-table :columns="logColumns" :data-source="logs" :loading="loading">
        <template #level="{ record }">
          <a-tag :type="getLogLevelType(record.level)">
            {{ record.level }}
          </a-tag>
        </template>
      </a-table>
    </a-card>

    <!-- 性能监控图表 -->
    <a-row :gutter="16">
      <a-col :span="12">
        <a-card>
          <template #title>资源使用趋势</template>
          <div ref="resourceChart" style="height: 300px"></div>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card>
          <template #title>日志分布</template>
          <div ref="logChart" style="height: 300px"></div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { Dayjs } from 'dayjs'
import type { MasterStatus } from '@/types/master'
import type { LogLevel, LogSource, LogRecord } from '@/types/log'

// 系统状态
const masterStatus = ref<MasterStatus>('running')
const stats = ref({
  onlineSlaves: 0,
  onlineDevices: 0,
  activeUsers: 0
})

// 日志查询参数
const dateRange = ref<[Dayjs, Dayjs]>()
const logLevel = ref<LogLevel>()
const logSource = ref<LogSource>()
const loading = ref(false)
const logs = ref<LogRecord[]>([])

// 图表实例
let resourceChart: echarts.ECharts | null = null
let logChart: echarts.ECharts | null = null

// 日志表格列定义
const logColumns = [
  { title: '时间', dataIndex: 'timestamp' },
  { title: '级别', dataIndex: 'level', slots: { customRender: 'level' } },
  { title: '来源', dataIndex: 'source' },
  { title: '消息', dataIndex: 'message' }
]

// 获取日志级别对应的标签类型
const getLogLevelType = (level: LogLevel): string => {
  switch (level) {
    case 'error': return 'danger'
    case 'warning': return 'warning'
    case 'info': return 'info'
    case 'debug': return 'default'
    default: return 'default'
  }
}

// 搜索日志
const searchLogs = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      ...(dateRange.value ? {
        startTime: dateRange.value[0].toISOString(),
        endTime: dateRange.value[1].toISOString()
      } : {}),
      ...(logLevel.value ? { level: logLevel.value } : {}),
      ...(logSource.value ? { source: logSource.value } : {})
    })

    const response = await fetch(`/api/logs?${params}`)
    const data = await response.json()
    logs.value = data.data.items
  } catch (error) {
    console.error('获取日志失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化图表
onMounted(() => {
  const resourceEl = document.querySelector('.resource-chart') as HTMLElement
  const logEl = document.querySelector('.log-chart') as HTMLElement

  if (resourceEl && logEl) {
    // 初始化资源使用趋势图表
    resourceChart = echarts.init(resourceEl)
    resourceChart.setOption({
      title: { text: '资源使用趋势' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['CPU使用率', '内存使用率', '磁盘使用率'] },
      xAxis: { type: 'time' },
      yAxis: { type: 'value', max: 100 },
      series: [
        {
          name: 'CPU使用率',
          type: 'line',
          data: []
        },
        {
          name: '内存使用率',
          type: 'line',
          data: []
        },
        {
          name: '磁盘使用率',
          type: 'line',
          data: []
        }
      ]
    })

    // 初始化日志分布图表
    logChart = echarts.init(logEl)
    logChart.setOption({
      title: { text: '日志分布' },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      series: [
        {
          type: 'pie',
          radius: ['50%', '70%'],
          data: [
            { value: 0, name: '错误' },
            { value: 0, name: '警告' },
            { value: 0, name: '信息' },
            { value: 0, name: '调试' }
          ]
        }
      ]
    })

    // 开始实时数据更新
    startRealTimeUpdate()
  }
})

// 清理图表实例
onUnmounted(() => {
  resourceChart?.dispose()
  logChart?.dispose()
  stopRealTimeUpdate()
})

// 实时数据更新
let updateTimer: ReturnType<typeof setInterval>
const startRealTimeUpdate = () => {
  updateTimer = setInterval(async () => {
    try {
      const [statsResponse, logsResponse] = await Promise.all([
        fetch('/api/master/stats'),
        fetch('/api/logs/stats')
      ])

      const [statsData, logsData] = await Promise.all([
        statsResponse.json(),
        logsResponse.json()
      ])

      // 更新统计数据
      stats.value = statsData.data
      
      // 更新图表
      updateCharts(statsData.data, logsData.data)
    } catch (error) {
      console.error('获取实时数据失败:', error)
    }
  }, 5000)
}

const stopRealTimeUpdate = () => {
  clearInterval(updateTimer)
}

// 更新图表数据
interface StatsData {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
}

interface LogsData {
  errorCount: number
  warningCount: number
  infoCount: number
  debugCount: number
}

const updateCharts = (statsData: StatsData, logsData: LogsData) => {
  // 更新资源使用趋势图表
  const timestamp = new Date().toISOString()
  const options = resourceChart?.getOption()
  if (options && Array.isArray(options.series)) {
    resourceChart?.setOption({
      series: [
        {
          data: [...(options.series[0].data || []), [timestamp, statsData.cpuUsage]]
        },
        {
          data: [...(options.series[1].data || []), [timestamp, statsData.memoryUsage]]
        },
        {
          data: [...(options.series[2].data || []), [timestamp, statsData.diskUsage]]
        }
      ]
    })
  }

  // 更新日志分布图表
  logChart?.setOption({
    series: [
      {
        data: [
          { value: logsData.errorCount, name: '错误' },
          { value: logsData.warningCount, name: '警告' },
          { value: logsData.infoCount, name: '信息' },
          { value: logsData.debugCount, name: '调试' }
        ]
      }
    ]
  })
}

// 初始化
onMounted(() => {
  searchLogs()
})
</script>

<style scoped>
.master-monitor {
  padding: 24px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style> 