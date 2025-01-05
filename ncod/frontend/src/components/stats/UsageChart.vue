<template>
  <div class="usage-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const props = defineProps<{
  data: {
    dates: string[]
    usage: number[]
    connections: number[]
  }
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  updateChart()
  
  // 响应式调整
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chart) return
  
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['使用时长(小时)', '连接次数']
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
      data: props.data.dates
    },
    yAxis: [
      {
        type: 'value',
        name: '使用时长(小时)',
        position: 'left'
      },
      {
        type: 'value',
        name: '连接次数',
        position: 'right'
      }
    ],
    series: [
      {
        name: '使用时长(小时)',
        type: 'line',
        smooth: true,
        data: props.data.usage,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '连接次数',
        type: 'bar',
        yAxisIndex: 1,
        data: props.data.connections,
        itemStyle: {
          color: '#67C23A'
        }
      }
    ]
  }
  
  chart.setOption(option)
}

const handleResize = () => {
  chart?.resize()
}

watch(() => props.data, updateChart, { deep: true })

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.usage-chart {
  width: 100%;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 400px;
}
</style> 