<template>
  <div class="slave-performance">
    <a-card class="mb-4">
      <template #title>从服务器性能监控</template>
      
      <!-- 性能指标概览 -->
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic title="CPU使用率" :value="metrics.cpuUsage" :precision="2" suffix="%">
            <template #prefix>
              <icon-cpu />
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="6">
          <a-statistic title="内存使用率" :value="metrics.memoryUsage" :precision="2" suffix="%">
            <template #prefix>
              <icon-memory />
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="6">
          <a-statistic title="磁盘使用率" :value="metrics.diskUsage" :precision="2" suffix="%">
            <template #prefix>
              <icon-disk />
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="6">
          <a-statistic title="设备连接数" :value="metrics.deviceCount">
            <template #prefix>
              <icon-usb />
            </template>
          </a-statistic>
        </a-col>
      </a-row>
    </a-card>

    <!-- 性能图表 -->
    <a-row :gutter="16">
      <a-col :span="12">
        <a-card>
          <template #title>CPU & 内存使用率趋势</template>
          <div ref="cpuMemChart" style="height: 300px"></div>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card>
          <template #title>网络流量趋势</template>
          <div ref="networkChart" style="height: 300px"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 设备状态 -->
    <a-card class="mt-4">
      <template #title>设备状态</template>
      <a-table :data="devices" :columns="deviceColumns" :pagination="false">
        <template #status="{ record }">
          <a-tag :color="record.status === 'online' ? 'green' : 'red'">
            {{ record.status }}
          </a-tag>
        </template>
      </a-table>
    </a-card>

    <!-- 告警信息 -->
    <a-card class="mt-4">
      <template #title>告警信息</template>
      <a-table :data="alerts" :columns="alertColumns">
        <template #type="{ record }">
          <a-tag :color="getAlertColor(record.type)">
            {{ record.type }}
          </a-tag>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import type { SlaveMetrics, SlaveAlert } from '@/types/slave'

const route = useRoute()
const slaveId = route.params.id as string

// 性能指标数据
const metrics = ref<SlaveMetrics>({
  cpuUsage: 0,
  memoryUsage: 0,
  diskUsage: 0,
  networkIn: 0,
  networkOut: 0,
  deviceCount: 0,
  activeConnections: 0,
  errorCount: 0,
  responseTime: 0,
  uptime: 0,
  usbBandwidth: 0,
  deviceErrors: 0,
  timestamp: new Date().toISOString()
})

// 设备列表数据
const devices = ref<any[]>([])

// 告警列表数据
const alerts = ref<SlaveAlert[]>([])

// 图表数据
const cpuMemChartData = ref<[string, number][]>([])
const networkChartData = ref<[string, number][]>([])

// 图表实例
let cpuMemChart: echarts.ECharts | null = null
let networkChart: echarts.ECharts | null = null

// 初始化图表
onMounted(() => {
  const cpuMemEl = document.querySelector('.cpu-mem-chart') as HTMLElement
  const networkEl = document.querySelector('.network-chart') as HTMLElement
  
  if (cpuMemEl && networkEl) {
    // 初始化CPU&内存图表
    cpuMemChart = echarts.init(cpuMemEl)
    cpuMemChart.setOption({
      title: { text: 'CPU & 内存使用率趋势' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['CPU使用率', '内存使用率'] },
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
        }
      ]
    })

    // 初始化网络流量图表
    networkChart = echarts.init(networkEl)
    networkChart.setOption({
      title: { text: '网络流量趋势' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['入流量', '出流量'] },
      xAxis: { type: 'time' },
      yAxis: { type: 'value' },
      series: [
        {
          name: '入流量',
          type: 'line',
          data: []
        },
        {
          name: '出流量',
          type: 'line',
          data: []
        }
      ]
    })

    // 开始实时数据更新
    startRealTimeUpdate()
  }
})

// 清理图表实例
onUnmounted(() => {
  cpuMemChart?.dispose()
  networkChart?.dispose()
  stopRealTimeUpdate()
})

// 实时数据更新
let updateTimer: ReturnType<typeof setInterval>
const startRealTimeUpdate = () => {
  updateTimer = setInterval(async () => {
    try {
      // 获取最新性能指标
      const response = await fetch(`/api/slaves/${slaveId}/metrics`)
      const data = await response.json()
      metrics.value = data

      // 更新图表数据
      updateCharts(data)
    } catch (error) {
      console.error('获取性能指标失败:', error)
    }
  }, 5000) // 每5秒更新一次
}

const stopRealTimeUpdate = () => {
  clearInterval(updateTimer)
}

// 更新图表数据
const updateCharts = (data: SlaveMetrics) => {
  const timestamp = data.timestamp
  
  // 更新CPU&内存图表
  cpuMemChart?.setOption({
    series: [
      {
        data: [...cpuMemChartData.value, [timestamp, data.cpuUsage]]
      },
      {
        data: [...cpuMemChartData.value, [timestamp, data.memoryUsage]]
      }
    ]
  })

  // 更新网络流量图表
  networkChart?.setOption({
    series: [
      {
        data: [...networkChartData.value, [timestamp, data.networkIn]]
      },
      {
        data: [...networkChartData.value, [timestamp, data.networkOut]]
      }
    ]
  })
}

// 设备列表配置
const deviceColumns = [
  { title: '设备名称', dataIndex: 'name' },
  { title: '设备类型', dataIndex: 'type' },
  { title: '状态', dataIndex: 'status', slots: { customRender: 'status' } },
  { title: '连接时间', dataIndex: 'connectedAt' }
]

// 告警列表配置
const alertColumns = [
  { title: '告警类型', dataIndex: 'type', slots: { customRender: 'type' } },
  { title: '告警信息', dataIndex: 'message' },
  { title: '发生时间', dataIndex: 'createdAt' },
  { title: '状态', dataIndex: 'status' }
]

// 获取告警标签颜色
const getAlertColor = (type: string) => {
  switch (type) {
    case 'error': return 'red'
    case 'warning': return 'orange'
    case 'info': return 'blue'
    default: return 'default'
  }
}
</script>

<style scoped>
.slave-performance {
  padding: 24px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}
</style> 