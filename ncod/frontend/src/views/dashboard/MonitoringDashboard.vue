<template>
  <div class="monitoring-dashboard">
    <a-row :gutter="[16, 16]">
      <!-- 性能指标卡片 -->
      <a-col :span="24">
        <a-card title="系统性能指标">
          <a-row :gutter="[16, 16]">
            <a-col :span="6">
              <a-statistic
                title="页面加载时间"
                :value="metrics.pageLoadTime"
                :precision="2"
                suffix="ms"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="首次内容绘制"
                :value="metrics.firstContentfulPaintTime"
                :precision="2"
                suffix="ms"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="内存使用率"
                :value="memoryUsagePercent"
                :precision="2"
                suffix="%"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="当前FPS"
                :value="currentFPS"
                :precision="0"
              />
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <!-- 资源加载性能 -->
      <a-col :span="12">
        <a-card title="资源加载性能">
          <a-table
            :columns="resourceColumns"
            :data-source="slowResources"
            :pagination="{ pageSize: 5 }"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'duration'">
                {{ record.duration.toFixed(2) }}ms
              </template>
              <template v-else-if="column.key === 'size'">
                {{ (record.transferSize / 1024).toFixed(2) }}KB
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <!-- 系统日志 -->
      <a-col :span="12">
        <a-card title="系统日志">
          <a-list
            :data-source="recentLogs"
            :pagination="{ pageSize: 5 }"
            size="small"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-tag :color="getLogTypeColor(item.type)">{{ item.type }}</a-tag>
                {{ item.module }} - {{ item.action }}
                <a-typography-text type="secondary">
                  {{ formatTime(item.timestamp) }}
                </a-typography-text>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>

      <!-- 设备状态概览 -->
      <a-col :span="24">
        <a-card title="设备状态概览">
          <a-row :gutter="[16, 16]">
            <a-col :span="6">
              <a-statistic
                title="在线设备"
                :value="deviceStats.online"
                :value-style="{ color: '#3f8600' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="离线设备"
                :value="deviceStats.offline"
                :value-style="{ color: '#cf1322' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="故障设备"
                :value="deviceStats.error"
                :value-style="{ color: '#faad14' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic
                title="总设备数"
                :value="deviceStats.total"
              />
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { TableColumnType } from 'ant-design-vue'
import performanceService from '@/utils/performance'
import type { PerformanceMetrics, ResourceTiming } from '@/utils/performance'
import type { LogEntry } from '@/utils/logger'
import { formatTime } from '@/utils/format'

// 性能指标
const metrics = ref<PerformanceMetrics>({
  pageLoadTime: 0,
  resourceLoadTime: 0,
  domContentLoadedTime: 0,
  firstPaintTime: 0,
  firstContentfulPaintTime: 0,
  largestContentfulPaintTime: 0,
  firstInputDelayTime: 0,
  cumulativeLayoutShift: 0
})

// 内存使用率
const memoryUsagePercent = ref(0)

// 当前FPS
const currentFPS = ref(60)

// 慢资源列表
const slowResources = ref<ResourceTiming[]>([])

// 资源表格列定义
const resourceColumns: TableColumnType[] = [
  {
    title: '资源名称',
    dataIndex: 'name',
    key: 'name',
    ellipsis: true
  },
  {
    title: '类型',
    dataIndex: 'initiatorType',
    key: 'type'
  },
  {
    title: '加载时间',
    dataIndex: 'duration',
    key: 'duration',
    sorter: (a, b) => a.duration - b.duration
  },
  {
    title: '大小',
    dataIndex: 'transferSize',
    key: 'size',
    sorter: (a, b) => a.transferSize - b.transferSize
  }
]

// 最近日志
const recentLogs = ref<LogEntry[]>([])

// 设备统计
const deviceStats = ref({
  online: 0,
  offline: 0,
  error: 0,
  total: 0
})

// 获取日志类型颜色
const getLogTypeColor = (type: string) => {
  switch (type) {
    case 'error':
      return 'red'
    case 'warning':
      return 'orange'
    default:
      return 'green'
  }
}

// 更新性能指标
const updateMetrics = () => {
  metrics.value = performanceService.collectMetrics()
  if (metrics.value.memoryUsage) {
    memoryUsagePercent.value =
      (metrics.value.memoryUsage.usedJSHeapSize / metrics.value.memoryUsage.jsHeapSizeLimit) * 100
  }
  slowResources.value = performanceService.analyzeResourcePerformance()
}

// 定时器
let metricsTimer: number

onMounted(() => {
  // 初始更新
  updateMetrics()
  
  // 定期更新性能指标
  metricsTimer = window.setInterval(updateMetrics, 5000)
  
  // TODO: 订阅WebSocket获取实时设备状态和日志更新
})

onUnmounted(() => {
  if (metricsTimer) {
    clearInterval(metricsTimer)
  }
  performanceService.stopMonitoring()
})
</script>

<style scoped>
.monitoring-dashboard {
  padding: 24px;
}
</style> 