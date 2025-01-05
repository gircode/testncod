<template>
  <div class="device-detail">
    <!-- 基本信息 -->
    <el-card class="detail-card">
      <template #header>
        <div class="card-header">
          <span>设备信息</span>
        </div>
      </template>
      <!-- 设备基本信息 -->
    </el-card>
    
    <!-- 实时统计 -->
    <el-card class="stats-card" v-if="currentStats">
      <template #header>
        <div class="card-header">
          <span>当前会话</span>
        </div>
      </template>
      
      <div class="current-session">
        <div class="session-info">
          <p>当前用户: {{ currentStats.current_session?.user?.username }}</p>
          <p>使用时长: {{ formatDuration(currentStats.current_session?.duration) }}</p>
          <p>开始时间: {{ formatDateTime(currentStats.current_session?.start_time) }}</p>
        </div>
      </div>
    </el-card>
    
    <!-- 总体统计 -->
    <el-card class="stats-card" v-if="totalStats">
      <template #header>
        <div class="card-header">
          <span>使用统计</span>
        </div>
      </template>
      
      <div class="total-stats">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ formatDuration(totalStats.total_usage_time) }}</div>
              <div class="stat-label">总使用时长</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ totalStats.connection_count }}</div>
              <div class="stat-label">连接次数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ totalStats.failed_connection_count }}</div>
              <div class="stat-label">失败次数</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <stats-card
          title="日使用时长"
          :value="formatDuration(totalStats?.daily_usage_time)"
          :trend="dailyUsageTrend"
          value-color="#409EFF"
        />
      </el-col>
      <el-col :span="6">
        <stats-card
          title="周使用时长"
          :value="formatDuration(totalStats?.weekly_usage_time)"
          :trend="weeklyUsageTrend"
          value-color="#67C23A"
        />
      </el-col>
      <el-col :span="6">
        <stats-card
          title="月使用时长"
          :value="formatDuration(totalStats?.monthly_usage_time)"
          :trend="monthlyUsageTrend"
          value-color="#E6A23C"
        />
      </el-col>
      <el-col :span="6">
        <stats-card
          title="连接成功率"
          :value="successRate + '%'"
          :trend="successRateTrend"
          value-color="#F56C6C"
        />
      </el-col>
    </el-row>
    
    <!-- 使用趋势图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>使用趋势</span>
          <el-radio-group v-model="timeRange" size="small">
            <el-radio-button label="week">周</el-radio-button>
            <el-radio-button label="month">月</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <usage-chart :data="chartData" />
    </el-card>
    
    <!-- 使用分布 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>用户使用分布</span>
            </div>
          </template>
          <usage-pie-chart :data="userDistributionData" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>设备利用率</span>
            </div>
          </template>
          <usage-gauge 
            :value="utilizationRate"
            title="设备利用率"
            :min="0"
            :max="100"
          />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 使用热力图 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>使用时段分布</span>
        </div>
      </template>
      <usage-heatmap :data="usageHeatmapData" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDeviceStore } from '@/store/device'
import { useStatsWebSocket } from '@/utils/stats-websocket'
import { useUserStore } from '@/store/user'
import { formatDuration, formatDateTime } from '@/utils/format'
import StatsCard from '@/components/stats/StatsCard.vue'
import UsageChart from '@/components/stats/UsageChart.vue'
import UsagePieChart from '@/components/stats/UsagePieChart.vue'
import UsageHeatmap from '@/components/stats/UsageHeatmap.vue'
import UsageGauge from '@/components/stats/UsageGauge.vue'

const props = defineProps<{
  deviceId: string
}>()

const deviceStore = useDeviceStore()
const userStore = useUserStore()

// 获取统计数据
const currentStats = computed(() => deviceStore.getDeviceStats(props.deviceId))
const totalStats = computed(() => currentStats.value?.total_stats)

// 连接WebSocket
onMounted(() => {
  const statsWs = useStatsWebSocket(userStore.currentUser.id)
  statsWs.connect()
})

onUnmounted(() => {
  const statsWs = useStatsWebSocket(userStore.currentUser.id)
  statsWs.disconnect()
})

const timeRange = ref('week')

// 计算趋势
const dailyUsageTrend = computed(() => 
  calculateTrend(totalStats?.daily_usage_time, totalStats?.previous_daily_usage_time)
)

const weeklyUsageTrend = computed(() => 
  calculateTrend(totalStats?.weekly_usage_time, totalStats?.previous_weekly_usage_time)
)

const monthlyUsageTrend = computed(() => 
  calculateTrend(totalStats?.monthly_usage_time, totalStats?.previous_monthly_usage_time)
)

const successRate = computed(() => {
  if (!totalStats) return 0
  const total = totalStats.connection_count + totalStats.failed_connection_count
  return total ? Math.round((totalStats.connection_count / total) * 100) : 0
})

const successRateTrend = computed(() => {
  if (!totalStats?.previous_success_rate) return 0
  return Math.round(
    ((successRate.value - totalStats.previous_success_rate) / totalStats.previous_success_rate) * 100
  )
})

// 图表数据
const chartData = computed(() => ({
  dates: totalStats?.usage_history?.dates || [],
  usage: totalStats?.usage_history?.usage || [],
  connections: totalStats?.usage_history?.connections || []
}))

function calculateTrend(current: number, previous: number): number {
  if (!current || !previous) return 0
  return Math.round(((current - previous) / previous) * 100)
}

// 用户使用分布数据
const userDistributionData = computed(() => ({
  labels: totalStats?.user_distribution?.map(item => item.username) || [],
  values: totalStats?.user_distribution?.map(item => item.usage_time) || []
}))

// 设备利用率
const utilizationRate = computed(() => {
  if (!totalStats) return 0
  const workingHours = 8 * 5 * 4 // 每月工作时长(8小时/天 * 5天/周 * 4周)
  return Math.min(100, Math.round((totalStats.monthly_usage_time / workingHours) * 100))
})

// 使用热力图数据
const usageHeatmapData = computed(() => ({
  hours: Array.from({ length: 24 }, (_, i) => `${i}:00`),
  days: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  values: totalStats?.usage_heatmap || Array(7).fill(Array(24).fill(0))
}))
</script>

<style scoped>
.device-detail {
  padding: 20px;
}

.detail-card, .stats-card {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  margin-top: 10px;
  color: #666;
}

.current-session {
  padding: 20px;
}

.session-info {
  line-height: 1.8;
}

.stats-cards {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 100%;
}
</style> 