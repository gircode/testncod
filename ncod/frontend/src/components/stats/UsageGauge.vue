<template>
  <div class="usage-gauge">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const props = defineProps<{
  value: number
  title: string
  min?: number
  max?: number
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  updateChart()
  
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chart) return
  
  const option: EChartsOption = {
    series: [{
      type: 'gauge',
      min: props.min || 0,
      max: props.max || 100,
      progress: {
        show: true,
        roundCap: true,
        width: 18
      },
      pointer: {
        show: false
      },
      axisLine: {
        roundCap: true,
        lineStyle: {
          width: 18
        }
      },
      axisTick: {
        show: false
      },
      splitLine: {
        show: false
      },
      axisLabel: {
        show: false
      },
      title: {
        show: true,
        fontSize: 14,
        offsetCenter: [0, '30%']
      },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, 0],
        fontSize: 30,
        formatter: '{value}%'
      },
      data: [{
        value: props.value,
        name: props.title
      }]
    }]
  }
  
  chart.setOption(option)
}

const handleResize = () => {
  chart?.resize()
}

watch(() => props.value, updateChart)
watch(() => props.title, updateChart)

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.usage-gauge {
  width: 100%;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 300px;
}
</style> 