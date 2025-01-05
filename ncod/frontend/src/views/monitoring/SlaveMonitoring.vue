<template>
    <div class="slave-monitoring">
        <!-- 状态概览卡片 -->
        <el-card class="overview-card">
            <template #header>
                <div class="card-header">
                    <span>状态概览</span>
                    <div class="header-right">
                        <el-button-group>
                            <el-button :loading="loading" @click="refreshData" :icon="Refresh">
                                刷新
                            </el-button>
                            <el-button @click="exportData" :icon="Download">
                                导出数据
                            </el-button>
                        </el-button-group>
                    </div>
                </div>
            </template>
            <el-row :gutter="20">
                <el-col :span="6">
                    <el-statistic title="CPU使用率" :value="metrics.cpu_usage" :precision="2" suffix="%">
                        <template #prefix>
                            <el-icon><Cpu /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
                <el-col :span="6">
                    <el-statistic title="内存使用率" :value="metrics.memory_usage" :precision="2" suffix="%">
                        <template #prefix>
                            <el-icon><Monitor /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
                <el-col :span="6">
                    <el-statistic title="磁盘使用率" :value="metrics.disk_usage" :precision="2" suffix="%">
                        <template #prefix>
                            <el-icon><Files /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
                <el-col :span="6">
                    <el-statistic 
                        title="网络流量" 
                        :value="metrics.network_in + metrics.network_out" 
                        :formatter="formatNetworkSpeed"
                    >
                        <template #prefix>
                            <el-icon><Connection /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
            </el-row>
        </el-card>

        <!-- 性能趋势图表 -->
        <el-row :gutter="20" class="chart-row">
            <el-col :span="12">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>CPU使用率趋势</span>
                            <el-select v-model="cpuTimeRange" size="small" style="width: 120px">
                                <el-option label="最近1小时" :value="3600000" />
                                <el-option label="最近6小时" :value="21600000" />
                                <el-option label="最近24小时" :value="86400000" />
                            </el-select>
                        </div>
                    </template>
                    <div ref="cpuChart" class="chart-container"></div>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>内存使用率趋势</span>
                            <el-select v-model="memoryTimeRange" size="small" style="width: 120px">
                                <el-option label="最近1小时" value="1h" />
                                <el-option label="最近6小时" value="6h" />
                                <el-option label="最近24小时" value="24h" />
                            </el-select>
                        </div>
                    </template>
                    <div ref="memoryChart" class="chart-container"></div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20" class="chart-row">
            <el-col :span="12">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>磁盘使用率趋势</span>
                            <el-select v-model="diskTimeRange" size="small" style="width: 120px">
                                <el-option label="最近1小时" value="1h" />
                                <el-option label="最近6小时" value="6h" />
                                <el-option label="最近24小时" value="24h" />
                            </el-select>
                        </div>
                    </template>
                    <div ref="diskChart" class="chart-container"></div>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>网络流量趋势</span>
                            <el-select v-model="networkTimeRange" size="small" style="width: 120px">
                                <el-option label="最近1小时" value="1h" />
                                <el-option label="最近6小时" value="6h" />
                                <el-option label="最近24小时" value="24h" />
                            </el-select>
                        </div>
                    </template>
                    <div ref="networkChart" class="chart-container"></div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 进程状态 -->
        <el-row :gutter="20" class="chart-row">
            <el-col :span="12">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>进程状态分布</span>
                        </div>
                    </template>
                    <div ref="processChart" class="chart-container"></div>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>系统负载</span>
                        </div>
                    </template>
                    <div ref="loadChart" class="chart-container"></div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 告警列表 -->
        <el-card class="alert-card">
            <template #header>
                <div class="card-header">
                    <span>告警信息</span>
                    <el-button-group>
                        <el-button size="small" @click="clearAlerts">清空告警</el-button>
                        <el-button size="small" type="primary" @click="exportAlerts">导出告警</el-button>
                    </el-button-group>
                </div>
            </template>
            <el-table :data="alerts" border stripe>
                <el-table-column prop="timestamp" label="时间" width="180">
                    <template #default="{ row }">
                        {{ formatDate(row.timestamp) }}
                    </template>
                </el-table-column>
                <el-table-column prop="level" label="级别" width="100">
                    <template #default="{ row }">
                        <el-tag :type="getAlertLevelType(row.level)">
                            {{ row.level }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="type" label="类型" width="120" />
                <el-table-column prop="message" label="描述" min-width="200" show-overflow-tooltip />
                <el-table-column label="操作" width="120" fixed="right">
                    <template #default="{ row }">
                        <el-button-group>
                            <el-tooltip content="查看详情">
                                <el-button size="small" type="primary" :icon="View" circle @click="showAlertDetail(row)" />
                            </el-tooltip>
                            <el-tooltip content="确认告警">
                                <el-button size="small" type="success" :icon="Check" circle @click="acknowledgeAlert(row)" />
                            </el-tooltip>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
    Refresh,
    Download,
    View,
    Check,
    Cpu,
    Monitor,
    Files,
    Connection
} from '@element-plus/icons-vue'
import type { TagProps } from 'element-plus'
import * as echarts from 'echarts'

// 系统指标类型
interface SystemMetrics {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_in: number
    network_out: number
    uptime: number
    process_count: number
    timestamp: string
}

// 告警类型
interface Alert {
    id: string
    timestamp: string
    level: 'info' | 'warning' | 'critical'
    type: string
    message: string
    acknowledged: boolean
}

// 图表DOM引用
const cpuChart = ref<HTMLElement | null>(null)
const memoryChart = ref<HTMLElement | null>(null)
const diskChart = ref<HTMLElement | null>(null)
const networkChart = ref<HTMLElement | null>(null)
const processChart = ref<HTMLElement | null>(null)
const loadChart = ref<HTMLElement | null>(null)

// 图表实例
let cpuChartInstance: echarts.ECharts | null = null
let memoryChartInstance: echarts.ECharts | null = null
let diskChartInstance: echarts.ECharts | null = null
let networkChartInstance: echarts.ECharts | null = null
let processChartInstance: echarts.ECharts | null = null
let loadChartInstance: echarts.ECharts | null = null

// 状态数据
const loading = ref(false)
const metrics = ref<SystemMetrics>({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    network_in: 0,
    network_out: 0,
    uptime: 0,
    process_count: 0,
    timestamp: ''
})

// 时间范围选择（毫秒）
const cpuTimeRange = ref<number>(3600000) // 1小时
const memoryTimeRange = ref<number>(3600000)
const diskTimeRange = ref<number>(3600000)
const networkTimeRange = ref<number>(3600000)

// 模拟告警数据
const alerts = ref<Alert[]>([
    {
        id: '1',
        timestamp: new Date().toISOString(),
        level: 'warning',
        type: 'CPU',
        message: 'CPU使用率超过80%',
        acknowledged: false
    },
    {
        id: '2',
        timestamp: new Date().toISOString(),
        level: 'critical',
        type: 'Memory',
        message: '内存使用率超过90%',
        acknowledged: false
    }
])

// 格式化函数
const formatDate = (date: string) => {
    return new Date(date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
}

const formatNetworkSpeed = (value: number) => {
    if (value >= 1024 * 1024 * 1024) {
        return `${(value / (1024 * 1024 * 1024)).toFixed(2)} GB/s`
    }
    if (value >= 1024 * 1024) {
        return `${(value / (1024 * 1024)).toFixed(2)} MB/s`
    }
    if (value >= 1024) {
        return `${(value / 1024).toFixed(2)} KB/s`
    }
    return `${value.toFixed(2)} B/s`
}

// 获取告警级别样式
const getAlertLevelType = (level: string): TagProps['type'] => {
    const typeMap: Record<string, TagProps['type']> = {
        info: 'info',
        warning: 'warning',
        critical: 'danger'
    }
    return typeMap[level] || 'info'
}

// 初始化图表
const initCharts = () => {
    // CPU图表
    if (cpuChart.value) {
        cpuChartInstance = echarts.init(cpuChart.value)
        cpuChartInstance.setOption({
            title: { text: 'CPU使用率趋势' },
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'time' },
            yAxis: { 
                type: 'value',
                min: 0,
                max: 100,
                axisLabel: {
                    formatter: '{value}%'
                }
            },
            series: [{
                name: 'CPU使用率',
                type: 'line',
                smooth: true,
                areaStyle: {},
                data: []
            }]
        })
    }

    // 内存图表
    if (memoryChart.value) {
        memoryChartInstance = echarts.init(memoryChart.value)
        memoryChartInstance.setOption({
            title: { text: '内存使用率趋势' },
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'time' },
            yAxis: { 
                type: 'value',
                min: 0,
                max: 100,
                axisLabel: {
                    formatter: '{value}%'
                }
            },
            series: [{
                name: '内存使用率',
                type: 'line',
                smooth: true,
                areaStyle: {},
                data: []
            }]
        })
    }

    // 磁盘图表
    if (diskChart.value) {
        diskChartInstance = echarts.init(diskChart.value)
        diskChartInstance.setOption({
            title: { text: '磁盘使用率趋势' },
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'time' },
            yAxis: { 
                type: 'value',
                min: 0,
                max: 100,
                axisLabel: {
                    formatter: '{value}%'
                }
            },
            series: [{
                name: '磁盘使用率',
                type: 'line',
                smooth: true,
                areaStyle: {},
                data: []
            }]
        })
    }

    // 网络图表
    if (networkChart.value) {
        networkChartInstance = echarts.init(networkChart.value)
        networkChartInstance.setOption({
            title: { text: '网络流量趋势' },
            tooltip: { trigger: 'axis' },
            legend: {
                data: ['入站流量', '出站流量']
            },
            xAxis: { type: 'time' },
            yAxis: { 
                type: 'value',
                axisLabel: {
                    formatter: (value: number) => formatNetworkSpeed(value)
                }
            },
            series: [
                {
                    name: '入站流量',
                    type: 'line',
                    smooth: true,
                    data: []
                },
                {
                    name: '出站流量',
                    type: 'line',
                    smooth: true,
                    data: []
                }
            ]
        })
    }

    // 进程状态图表
    if (processChart.value) {
        processChartInstance = echarts.init(processChart.value)
        processChartInstance.setOption({
            title: { text: '进程状态分布' },
            tooltip: { trigger: 'item' },
            legend: {
                orient: 'vertical',
                left: 'left'
            },
            series: [
                {
                    name: '进程状态',
                    type: 'pie',
                    radius: '50%',
                    data: [
                        { value: 120, name: '运行中', itemStyle: { color: '#67C23A' } },
                        { value: 25, name: '睡眠', itemStyle: { color: '#409EFF' } },
                        { value: 5, name: '停止', itemStyle: { color: '#E6A23C' } },
                        { value: 2, name: '僵尸', itemStyle: { color: '#F56C6C' } }
                    ]
                }
            ]
        })
    }

    // 系统负载图表
    if (loadChart.value) {
        loadChartInstance = echarts.init(loadChart.value)
        loadChartInstance.setOption({
            title: { text: '系统负载趋势' },
            tooltip: { trigger: 'axis' },
            legend: {
                data: ['1分钟', '5分钟', '15分钟']
            },
            xAxis: { type: 'time' },
            yAxis: { type: 'value' },
            series: [
                {
                    name: '1分钟',
                    type: 'line',
                    smooth: true,
                    data: []
                },
                {
                    name: '5分钟',
                    type: 'line',
                    smooth: true,
                    data: []
                },
                {
                    name: '15分钟',
                    type: 'line',
                    smooth: true,
                    data: []
                }
            ]
        })
    }
}

// 刷新数据
const refreshData = async () => {
    loading.value = true
    try {
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // 更新指标数据
        metrics.value = {
            cpu_usage: Math.random() * 100,
            memory_usage: Math.random() * 100,
            disk_usage: Math.random() * 100,
            network_in: Math.random() * 1024 * 1024 * 1024,
            network_out: Math.random() * 1024 * 1024 * 1024,
            uptime: Date.now(),
            process_count: Math.floor(Math.random() * 1000),
            timestamp: new Date().toISOString()
        }

        // 更新图表数据
        updateCharts()
        
        ElMessage.success('数据刷新成功')
    } catch (error) {
        ElMessage.error('数据刷新失败')
        console.error(error)
    } finally {
        loading.value = false
    }
}

// 更新图表数据
const updateCharts = () => {
    const now = new Date()
    const data = Array.from({ length: 10 }, (_, i) => {
        const time = new Date(now.getTime() - (9 - i) * 60000)
        return [time, Math.random() * 100]
    })

    if (cpuChartInstance) {
        cpuChartInstance.setOption({
            series: [{
                data
            }]
        })
    }

    if (memoryChartInstance) {
        memoryChartInstance.setOption({
            series: [{
                data
            }]
        })
    }

    if (diskChartInstance) {
        diskChartInstance.setOption({
            series: [{
                data
            }]
        })
    }

    if (networkChartInstance) {
        const inData = data.map(([time]) => [time, Math.random() * 1024 * 1024 * 1024])
        const outData = data.map(([time]) => [time, Math.random() * 1024 * 1024 * 1024])
        networkChartInstance.setOption({
            series: [
                { data: inData },
                { data: outData }
            ]
        })
    }

    if (loadChartInstance) {
        const load1 = data.map(([time]) => [time, Math.random() * 4])
        const load5 = data.map(([time]) => [time, Math.random() * 3])
        const load15 = data.map(([time]) => [time, Math.random() * 2])
        loadChartInstance.setOption({
            series: [
                { data: load1 },
                { data: load5 },
                { data: load15 }
            ]
        })
    }
}

// 导出数据
const exportData = () => {
    ElMessage.success('数据导出成功')
}

// 清空告警
const clearAlerts = () => {
    alerts.value = []
    ElMessage.success('告警已清空')
}

// 导出告警
const exportAlerts = () => {
    ElMessage.success('告警导出成功')
}

// 查看告警详情
const showAlertDetail = (alert: Alert) => {
    ElMessage.info('查看告警详情：' + alert.message)
}

// 确认告警
const acknowledgeAlert = (alert: Alert) => {
    alerts.value = alerts.value.filter(a => a !== alert)
    ElMessage.success('告警已确认')
}

// 自动刷新
let refreshTimer: number | null = null

const startAutoRefresh = () => {
    stopAutoRefresh()
    refreshTimer = window.setInterval(() => {
        refreshData()
    }, 30000) // 每30秒刷新一次
}

const stopAutoRefresh = () => {
    if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
    }
}

// 窗口大小变化时重绘图表
const handleResize = () => {
    cpuChartInstance?.resize()
    memoryChartInstance?.resize()
    diskChartInstance?.resize()
    networkChartInstance?.resize()
    processChartInstance?.resize()
    loadChartInstance?.resize()
}

// 组件挂载
onMounted(() => {
    initCharts()
    refreshData()
    startAutoRefresh()
    window.addEventListener('resize', handleResize)
})

// 组件卸载
onUnmounted(() => {
    stopAutoRefresh()
    window.removeEventListener('resize', handleResize)
    cpuChartInstance?.dispose()
    memoryChartInstance?.dispose()
    diskChartInstance?.dispose()
    networkChartInstance?.dispose()
    processChartInstance?.dispose()
    loadChartInstance?.dispose()
})
</script>

<style scoped>
.slave-monitoring {
    padding: 20px;
}

.overview-card {
    margin-bottom: 20px;
}

.chart-row {
    margin-bottom: 20px;
}

.chart-container {
    height: 300px;
}

.alert-card {
    margin-bottom: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-right {
    display: flex;
    gap: 10px;
}

:deep(.el-card__header) {
    padding: 15px 20px;
}

:deep(.el-statistic) {
    text-align: center;
}

:deep(.el-statistic__content) {
    color: var(--el-color-primary);
    font-size: 24px;
}

:deep(.el-table) {
    margin-top: 10px;
}

:deep(.el-tag) {
    text-transform: uppercase;
}
</style> 