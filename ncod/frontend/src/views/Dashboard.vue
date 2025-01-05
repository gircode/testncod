<!-- 仪表盘 -->
<template>
    <div class="dashboard">
        <el-row :gutter="20">
            <!-- 设备统计卡片 -->
            <el-col :span="8">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>设备统计</span>
                        </div>
                    </template>
                    <div class="card-content">
                        <el-row>
                            <el-col :span="12">
                                <div class="stat-item">
                                    <div class="stat-title">总设备数</div>
                                    <div class="stat-value">{{ stats.totalDevices }}</div>
                                </div>
                            </el-col>
                            <el-col :span="12">
                                <div class="stat-item">
                                    <div class="stat-title">在线设备</div>
                                    <div class="stat-value">{{ stats.onlineDevices }}</div>
                                </div>
                            </el-col>
                        </el-row>
                    </div>
                </el-card>
            </el-col>

            <!-- 从机统计卡片 -->
            <el-col :span="8">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>从机统计</span>
                        </div>
                    </template>
                    <div class="card-content">
                        <el-row>
                            <el-col :span="12">
                                <div class="stat-item">
                                    <div class="stat-title">总从机数</div>
                                    <div class="stat-value">{{ stats.totalSlaves }}</div>
                                </div>
                            </el-col>
                            <el-col :span="12">
                                <div class="stat-item">
                                    <div class="stat-title">在线从机</div>
                                    <div class="stat-value">{{ stats.onlineSlaves }}</div>
                                </div>
                            </el-col>
                        </el-row>
                    </div>
                </el-card>
            </el-col>

            <!-- 用户统计卡片 -->
            <el-col :span="8">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>用户统计</span>
                        </div>
                    </template>
                    <div class="card-content">
                        <el-row>
                            <el-col :span="12">
                                <div class="stat-item">
                                    <div class="stat-title">总用户数</div>
                                    <div class="stat-value">{{ stats.totalUsers }}</div>
                                </div>
                            </el-col>
                            <el-col :span="12">
                                <div class="stat-item">
                                    <div class="stat-title">在线用户</div>
                                    <div class="stat-value">{{ stats.onlineUsers }}</div>
                                </div>
                            </el-col>
                        </el-row>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 设备状态图表 -->
        <el-row :gutter="20" class="chart-row">
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>设备状态分布</span>
                        </div>
                    </template>
                    <div ref="deviceChart" class="chart"></div>
                </el-card>
            </el-col>

            <!-- 从机状态图表 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>从机状态监控</span>
                        </div>
                    </template>
                    <div ref="slaveChart" class="chart"></div>
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { http } from '@/utils/http'

const stats = ref({
    totalDevices: 0,
    onlineDevices: 0,
    totalSlaves: 0,
    onlineSlaves: 0,
    totalUsers: 0,
    onlineUsers: 0
})

const deviceChart = ref<HTMLElement>()
const slaveChart = ref<HTMLElement>()
let deviceChartInstance: echarts.ECharts | null = null
let slaveChartInstance: echarts.ECharts | null = null

// 模拟获取统计数据
const fetchStats = async () => {
    try {
        // 实际项目中这里应该调用后端API
        stats.value = {
            totalDevices: 100,
            onlineDevices: 85,
            totalSlaves: 20,
            onlineSlaves: 18,
            totalUsers: 50,
            onlineUsers: 30
        }
    } catch (error) {
        console.error('获取统计数据失败:', error)
    }
}

// 初始化设备状态图表
const initDeviceChart = () => {
    if (deviceChart.value) {
        deviceChartInstance = echarts.init(deviceChart.value)
        const option = {
            tooltip: {
                trigger: 'item'
            },
            legend: {
                orient: 'vertical',
                left: 'left'
            },
            series: [
                {
                    name: '设备状态',
                    type: 'pie',
                    radius: '50%',
                    data: [
                        { value: 85, name: '在线' },
                        { value: 15, name: '离线' }
                    ],
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        }
        deviceChartInstance.setOption(option)
    }
}

// 初始化从机状态图表
const initSlaveChart = () => {
    if (slaveChart.value) {
        slaveChartInstance = echarts.init(slaveChart.value)
        const option = {
            tooltip: {
                trigger: 'axis'
            },
            xAxis: {
                type: 'category',
                data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            },
            yAxis: {
                type: 'value'
            },
            series: [
                {
                    name: '在线从机数',
                    type: 'line',
                    data: [18, 17, 19, 18, 18, 20, 19]
                }
            ]
        }
        slaveChartInstance.setOption(option)
    }
}

// 处理窗口大小变化
const handleResize = () => {
    deviceChartInstance?.resize()
    slaveChartInstance?.resize()
}

onMounted(() => {
    fetchStats()
    initDeviceChart()
    initSlaveChart()
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    deviceChartInstance?.dispose()
    slaveChartInstance?.dispose()
})
</script>

<style scoped>
.dashboard {
    padding: 20px;
}

.chart-row {
    margin-top: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-content {
    text-align: center;
}

.stat-item {
    padding: 10px;
}

.stat-title {
    font-size: 14px;
    color: #909399;
}

.stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
    margin-top: 5px;
}

.chart {
    height: 300px;
}
</style>