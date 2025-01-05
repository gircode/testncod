<template>
  <div class="usage-heatmap">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const props = defineProps<{
  data: {
    hours: string[]
    days: string[]
    values: number[][]
  }
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
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        return `${params.name}<br/>使用时长: ${params.value[2].toFixed(2)}小时`
      }
    },
    grid: {
      top: '10%',
      left: '5%',
      right: '5%',
      bottom: '10%'
    },
    xAxis: {
      type: 'category',
      data: props.data.hours,
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: props.data.days,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: Math.max(...props.data.values.flat()),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#e9f7f4', '#58c9b9', '#317589']
      }
    },
    series: [{
      type: 'heatmap',
      data: props.data.values.map((row, i) => 
        row.map((val, j) => [j, i, val])
      ).flat(),
      label: {
        show: false
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
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
.usage-heatmap {
  width: 100%;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 400px;
}
</style> 