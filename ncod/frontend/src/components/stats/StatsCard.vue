<template>
  <el-card class="stats-card" :body-style="{ padding: '0px' }">
    <div class="stats-header">
      <div class="title">{{ title }}</div>
      <div class="value" :style="{ color: valueColor }">{{ value }}</div>
    </div>
    <div class="stats-trend">
      <div class="trend-value" :class="trendClass">
        <el-icon>
          <component :is="trendIcon" />
        </el-icon>
        {{ trend }}%
      </div>
      <div class="trend-label">较上周</div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const props = defineProps<{
  title: string
  value: string | number
  trend: number
  valueColor?: string
}>()

const trendClass = computed(() => ({
  'trend-up': props.trend > 0,
  'trend-down': props.trend < 0
}))

const trendIcon = computed(() => 
  props.trend > 0 ? ArrowUp : ArrowDown
)
</script>

<style scoped>
.stats-card {
  height: 120px;
}

.stats-header {
  padding: 20px;
}

.title {
  font-size: 14px;
  color: #666;
}

.value {
  font-size: 24px;
  font-weight: bold;
  margin-top: 8px;
}

.stats-trend {
  padding: 10px 20px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
}

.trend-value {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.trend-up {
  color: #67C23A;
}

.trend-down {
  color: #F56C6C;
}

.trend-label {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}
</style> 