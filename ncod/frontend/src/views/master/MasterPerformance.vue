<template>
  <div class="master-performance">
    <!-- 系统性能概览 -->
    <a-card class="mb-4">
      <template #title>系统性能概览</template>
      
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
          <a-statistic title="在线从服务器" :value="metrics.onlineSlaves">
            <template #prefix>
              <icon-server />
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="6">
          <a-statistic title="总设备数" :value="metrics.totalDevices">
            <template #prefix>
              <icon-usb />
            </template>
          </a-statistic>
        </a-col>
      </a-row>
    </a-card>

    <!-- 性能趋势图表 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :span="12">
        <a-card>
          <template #title>系统资源使用趋势</template>
          <div ref="systemChart" style="height: 300px"></div>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card>
          <template #title>从服务器状态分布</template>
          <div ref="slaveChart" style="height: 300px"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 从服务器状态列表 -->
    <a-card>
      <template #title>从服务器状态</template>
      <template #extra>
        <a-radio-group v-model="filterStatus" button-style="solid">
          <a-radio-button value="">全部</a-radio-button>
          <a-radio-button value="online">在线</a-radio-button>
          <a-radio-button value="offline">离线</a-radio-button>
          <a-radio-button value="warning">告警</a-radio-button>
        </a-radio-group>
      </template>

      <a-table :columns="slaveColumns" :data-source="filteredSlaves">
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ record.status }}
          </a-tag>
        </template>
        
        <template #cpuUsage="{ record }">
          <a-progress
            :percent="record.cpuUsage"
            :status="getResourceStatus(record.cpuUsage)"
            size="small"
          />
        </template>
        
        <template #memoryUsage="{ record }">
          <a-progress
            :percent="record.memoryUsage"
            :status="getResourceStatus(record.memoryUsage)"
            size="small"
          />
        </template>
        
        <template #action="{ record }">
          <a-button type="link" @click="viewSlaveDetail(record)">
            查看详情
          </a-button>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import type { MasterMetrics, SlaveStatus, SlaveInfo } from '@/types/master'

const router = useRouter()

// 系统性能指标
const metrics = ref<MasterMetrics>({
  cpuUsage: 0,
  memoryUsage: 0,
  onlineSlaves: 0,
  totalDevices: 0,
  timestamp: new Date().toISOString()
})

// 从服务器列表
const slaves = ref<SlaveInfo[]>([])
const filterStatus = ref('')

// 图表实例
let systemChart: echarts.ECharts | null = null
let slaveChart: echarts.ECharts | null = null

// 从服务器列表列定义
const slaveColumns = [
  { title: '名称', dataIndex: 'name' },
  { title: '状态', dataIndex: 'status', slots: { customRender: 'status' } },
  { title: 'CPU使用率', dataIndex: 'cpuUsage', slots: { customRender: 'cpuUsage' } },
  { title: '内存使用率', dataIndex: 'memoryUsage', slots: { customRender: 'memoryUsage' } },
  { title: '设备数', dataIndex: 'deviceCount' },
  { title: '操作', slots: { customRender: 'action' } }
]

// 过滤后的从服务器列表
const filteredSlaves = computed(() => {
  if (!filterStatus.value) return slaves.value
  return slaves.value.filter(slave => slave.status === filterStatus.value)
})

// 初始化图表
onMounted(() => {
  const systemEl = document.querySelector('.system-chart') as HTMLElement
  const slaveEl = document.querySelector('.slave-chart') as HTMLElement
  
  if (systemEl && slaveEl) {
    // 初始化系统资源图表
    systemChart = echarts.init(systemEl)
    systemChart.setOption({
      title: { text: '系统资源使用趋势' },
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

    // 初始化从服务器状态分布图表
    slaveChart = echarts.init(slaveEl)
    slaveChart.setOption({
      title: { text: '从服务器状态分布' },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      series: [
        {
          type: 'pie',
          radius: ['50%', '70%'],
          data: [
            { value: 0, name: '在线' },
            { value: 0, name: '离线' },
            { value: 0, name: '告警' }
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
  systemChart?.dispose()
  slaveChart?.dispose()
  stopRealTimeUpdate()
})

// 实时数据更新
let updateTimer: ReturnType<typeof setInterval>
const startRealTimeUpdate = () => {
  updateTimer = setInterval(async () => {
    try {
      // 获取最新性能指标
      const [metricsResponse, slavesResponse] = await Promise.all([
        fetch('/api/master/metrics'),
        fetch('/api/master/slaves')
      ])
      
      const [metricsData, slavesData] = await Promise.all([
        metricsResponse.json(),
        slavesResponse.json()
      ])

      metrics.value = metricsData
      slaves.value = slavesData

      // 更新图表
      updateCharts()
    } catch (error) {
      console.error('获取性能指标失败:', error)
    }
  }, 5000)
}

const stopRealTimeUpdate = () => {
  clearInterval(updateTimer)
}

// 更新图表数据
const updateCharts = () => {
  const timestamp = metrics.value.timestamp
  
  // 更新系统资源图表
  const systemOptions = systemChart?.getOption()
  if (systemOptions && Array.isArray(systemOptions.series)) {
    systemChart?.setOption({
      series: [
        {
          data: [...(systemOptions.series[0].data || []), [timestamp, metrics.value.cpuUsage]]
        },
        {
          data: [...(systemOptions.series[1].data || []), [timestamp, metrics.value.memoryUsage]]
        }
      ]
    })
  }

  // 更新从服务器状态分布图表
  const statusCount = {
    online: slaves.value.filter(s => s.status === 'online').length,
    offline: slaves.value.filter(s => s.status === 'offline').length,
    warning: slaves.value.filter(s => s.status === 'warning').length
  }

  slaveChart?.setOption({
    series: [
      {
        data: [
          { value: statusCount.online, name: '在线' },
          { value: statusCount.offline, name: '离线' },
          { value: statusCount.warning, name: '告警' }
        ]
      }
    ]
  })
}

// 获取状态标签颜色
const getStatusColor = (status: SlaveStatus) => {
  switch (status) {
    case 'online': return 'green'
    case 'offline': return 'red'
    case 'warning': return 'orange'
    default: return 'default'
  }
}

// 获取资源使用状态
const getResourceStatus = (usage: number) => {
  if (usage >= 90) return 'exception'
  if (usage >= 80) return 'warning'
  return 'normal'
}

// 查看从服务器详情
const viewSlaveDetail = (slave: SlaveInfo) => {
  router.push(`/slaves/${slave.id}/performance`)
}
</script>

<style scoped>
.master-performance {
  padding: 24px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style> 