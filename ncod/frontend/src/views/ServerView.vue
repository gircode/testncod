<template>
    <div class="server-view">
        <!-- 过滤工具栏 -->
        <div class="filter-bar">
            <el-row :gutter="20">
                <el-col :span="6">
                    <el-input v-model="searchQuery" placeholder="搜索服务器名称" clearable prefix-icon="Search" />
                </el-col>
                <el-col :span="6">
                    <el-select v-model="statusFilter" placeholder="服务器状态" clearable>
                        <el-option label="在线" value="online" />
                        <el-option label="离线" value="offline" />
                        <el-option label="警告" value="warning" />
                        <el-option label="错误" value="error" />
                    </el-select>
                </el-col>
                <el-col :span="12" style="text-align: right">
                    <el-button-group>
                        <el-button type="primary" @click="refreshData">
                            <el-icon>
                                <Refresh />
                            </el-icon>
                            刷新数据
                        </el-button>
                        <el-button type="success" @click="exportData">
                            <el-icon>
                                <Download />
                            </el-icon>
                            导出数据
                        </el-button>
                        <el-button type="warning" @click="showBatchOperation">
                            <el-icon>
                                <Operation />
                            </el-icon>
                            批量操作
                        </el-button>
                    </el-button-group>
                </el-col>
            </el-row>
        </div>

        <!-- 服务器状态概览 -->
        <el-row :gutter="20" class="status-overview">
            <el-col :span="6">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>
                                <el-icon>
                                    <Monitor />
                                </el-icon>
                                总服务器数
                            </span>
                        </div>
                    </template>
                    <div class="card-content">
                        {{ store.serverList.length }}
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>
                                <el-icon>
                                    <CircleCheck />
                                </el-icon>
                                在线服务器
                            </span>
                        </div>
                    </template>
                    <div class="card-content success">
                        {{ store.onlineServers }}
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>
                                <el-icon>
                                    <Warning />
                                </el-icon>
                                警告服务器
                            </span>
                        </div>
                    </template>
                    <div class="card-content warning">
                        {{ store.warningServers }}
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>
                                <el-icon>
                                    <CircleClose />
                                </el-icon>
                                错误服务器
                            </span>
                        </div>
                    </template>
                    <div class="card-content danger">
                        {{ store.errorServers }}
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 性能监控图表 -->
        <el-row :gutter="20" class="performance-charts">
            <!-- 系统资源趋势图 -->
            <el-col :span="24">
                <el-card class="chart-card">
                    <template #header>
                        <div class="chart-header">
                            <span>
                                <el-icon>
                                    <DataLine />
                                </el-icon>
                                系统资源使用趋势
                            </span>
                            <el-radio-group v-model="trendTimeRange" size="small">
                                <el-radio-button label="1h">1小时</el-radio-button>
                                <el-radio-button label="6h">6小时</el-radio-button>
                                <el-radio-button label="24h">24小时</el-radio-button>
                            </el-radio-group>
                        </div>
                    </template>
                    <div ref="trendChartRef" class="chart"></div>
                </el-card>
            </el-col>

            <!-- 性能指标仪表盘 -->
            <el-col :span="24">
                <el-card class="chart-card">
                    <template #header>
                        <div class="chart-header">
                            <span>
                                <el-icon>
                                    <Histogram />
                                </el-icon>
                                性能指标仪表盘
                            </span>
                        </div>
                    </template>
                    <div class="dashboard-grid">
                        <div class="dashboard-item">
                            <div ref="cpuGaugeRef" class="gauge-chart"></div>
                            <div class="gauge-label">
                                <el-icon>
                                    <Cpu />
                                </el-icon>
                                CPU使用率
                            </div>
                        </div>
                        <div class="dashboard-item">
                            <div ref="memoryGaugeRef" class="gauge-chart"></div>
                            <div class="gauge-label">
                                <el-icon>
                                    <Loading />
                                </el-icon>
                                内存使用率
                            </div>
                        </div>
                        <div class="dashboard-item">
                            <div ref="diskGaugeRef" class="gauge-chart"></div>
                            <div class="gauge-label">
                                <el-icon>
                                    <More />
                                </el-icon>
                                磁盘使用率
                            </div>
                        </div>
                        <div class="dashboard-item">
                            <div ref="networkGaugeRef" class="gauge-chart"></div>
                            <div class="gauge-label">
                                <el-icon>
                                    <Connection />
                                </el-icon>
                                网络带宽使用率
                            </div>
                        </div>
                    </div>
                </el-card>
            </el-col>

            <!-- 网络流量监控 -->
            <el-col :span="12">
                <el-card class="chart-card">
                    <template #header>
                        <div class="chart-header">
                            <span>
                                <el-icon>
                                    <Connection />
                                </el-icon>
                                网络流量
                            </span>
                            <div class="network-info">
                                <span>
                                    <el-icon>
                                        <UploadFilled />
                                    </el-icon>
                                    上传：{{ formatBitrate(store.currentMetrics?.network.bandwidth.out || 0) }}
                                </span>
                                <span>
                                    <el-icon>
                                        <Download />
                                    </el-icon>
                                    下载：{{ formatBitrate(store.currentMetrics?.network.bandwidth.in || 0) }}
                                </span>
                            </div>
                        </div>
                    </template>
                    <div ref="networkChartRef" class="chart"></div>
                </el-card>
            </el-col>

            <!-- 系统运行状态 -->
            <el-col :span="12">
                <el-card class="chart-card">
                    <template #header>
                        <div class="chart-header">
                            <span>
                                <el-icon>
                                    <Timer />
                                </el-icon>
                                系统运行状态
                            </span>
                            <div class="system-info">
                                <span>运行时间：{{ formatDurationSeconds(store.currentMetrics?.system.uptime || 0) }}</span>
                            </div>
                        </div>
                    </template>
                    <div class="system-status">
                        <el-row :gutter="20">
                            <el-col :span="8">
                                <div class="status-item">
                                    <div class="status-label">CPU温度</div>
                                    <el-progress type="dashboard" :percentage="cpuTemperaturePercentage"
                                        :color="getTemperatureColor(store.currentMetrics?.cpu.temperature || 0)">
                                        <template #default>
                                            <span class="temperature-text">
                                                {{ formatTemperature(store.currentMetrics?.cpu.temperature || 0) }}
                                            </span>
                                        </template>
                                    </el-progress>
                                </div>
                            </el-col>
                            <el-col :span="8">
                                <div class="status-item">
                                    <div class="status-label">进程数</div>
                                    <div class="status-value">
                                        {{ store.currentMetrics?.system.processes || 0 }}
                                        <small>进程</small>
                                    </div>
                                    <div class="status-subvalue">
                                        {{ store.currentMetrics?.system.threads || 0 }} 线程
                                    </div>
                                </div>
                            </el-col>
                            <el-col :span="8">
                                <div class="status-item">
                                    <div class="status-label">启动时间</div>
                                    <div class="status-value">
                                        {{ store.currentMetrics?.system.bootTime || '-' }}
                                    </div>
                                </div>
                            </el-col>
                        </el-row>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 服务器列表 -->
        <el-card class="server-list">
            <template #header>
                <div class="card-header">
                    <span>
                        <el-icon>
                            <Monitor />
                        </el-icon>
                        服务器列表
                    </span>
                </div>
            </template>
            <el-table :data="filteredServers" v-loading="store.loading.servers" style="width: 100%">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="name" label="服务器名称" />
                <el-table-column prop="ip" label="IP地址" />
                <el-table-column prop="status" label="状态">
                    <template #default="{ row }">
                        <el-tag
                            :type="row.status === 'online' ? 'success' : row.status === 'warning' ? 'warning' : 'danger'">
                            {{ row.status === 'online' ? '在线' : row.status === 'warning' ? '警告' : '错误' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="CPU使用率">
                    <template #default="{ row }">
                        <el-progress :percentage="row.metrics?.cpu.usage || 0"
                            :color="getMetricColor(row.metrics?.cpu.usage || 0)" />
                    </template>
                </el-table-column>
                <el-table-column label="内存使用率">
                    <template #default="{ row }">
                        <el-progress :percentage="row.metrics?.memory.usage || 0"
                            :color="getMetricColor(row.metrics?.memory.usage || 0)" />
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                    <template #default="{ row }">
                        <el-button-group>
                            <el-button size="small" :type="row.status === 'online' ? 'danger' : 'success'"
                                @click="handleServerOperation(row, row.status === 'online' ? 'stop' : 'start')">
                                {{ row.status === 'online' ? '停止' : '启动' }}
                            </el-button>
                            <el-button size="small" type="primary" @click="handleViewDetails(row)">
                                详情
                            </el-button>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <!-- 批量操作对话框 -->
        <el-dialog v-model="batchDialogVisible" title="批量操作" width="50%">
            <el-form :model="batchForm" label-width="100px">
                <el-form-item label="操作类型">
                    <el-select v-model="batchForm.operation" placeholder="请选择操作类型">
                        <el-option label="启动服务器" value="start" />
                        <el-option label="停止服务器" value="stop" />
                        <el-option label="重启服务器" value="restart" />
                        <el-option label="更新配置" value="update-config" />
                        <el-option label="同步时间" value="sync-time" />
                        <el-option label="清理缓存" value="clear-cache" />
                        <el-option label="检查更新" value="check-update" />
                        <el-option label="安装更新" value="install-update" />
                        <el-option label="系统优化" value="optimize" />
                    </el-select>
                </el-form-item>
                <el-form-item label="选择服务器">
                    <el-transfer v-model="batchForm.selectedServers" :data="store.serverList.map(server => ({
                        key: server.id,
                        label: server.name
                    }))" :titles="['可选服务器', '已选服务器']" :button-texts="['移除', '添加']" :format="{
                        noChecked: '${total}',
                        hasChecked: '${checked}/${total}'
                    }" />
                </el-form-item>
                <el-form-item label="执行时间">
                    <el-radio-group v-model="batchForm.executeTime">
                        <el-radio label="immediate">立即执行</el-radio>
                        <el-radio label="scheduled">定时执行</el-radio>
                    </el-radio-group>
                </el-form-item>
                <el-form-item v-if="batchForm.executeTime === 'scheduled'" label="计划时间">
                    <el-date-picker v-model="batchForm.scheduledTime" type="datetime" placeholder="选择执行时间" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="batchDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="executeBatchOperation">
                        确认
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useServerStore } from '@/stores/server'
import type { ServerMetrics, ServerStatus } from '@/stores/server'
import { ElMessage } from 'element-plus'
import {
    DataLine,
    Histogram,
    Cpu,
    Loading,
    More,
    Connection,
    Timer,
    Download,
    Search,
    Refresh,
    Operation,
    Monitor,
    CircleCheck,
    Warning,
    CircleClose,
    Setting,
    UploadFilled
} from '@element-plus/icons-vue'
import { formatBytes, formatBitrate, formatDurationSeconds, formatTemperature } from '@/utils/format'
import { useWebSocket } from '@/composables/useWebSocket'
import type { WebSocketInstance } from '@/composables/useWebSocket'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import '@/assets/styles/server.css'

interface BatchForm {
    operation: string
    selectedServers: string[]
    executeTime: 'immediate' | 'scheduled'
    scheduledTime: Date | null
}

const store = useServerStore()
const searchQuery = ref('')
const statusFilter = ref('')
const batchDialogVisible = ref(false)
const trendTimeRange = ref('1h')

// 批量操作表单
const batchForm = ref<BatchForm>({
    operation: '',
    selectedServers: [],
    executeTime: 'immediate',
    scheduledTime: null
})

// 图表实例引用
const trendChartRef = ref<HTMLElement>()
const cpuGaugeRef = ref<HTMLElement>()
const memoryGaugeRef = ref<HTMLElement>()
const diskGaugeRef = ref<HTMLElement>()
const networkGaugeRef = ref<HTMLElement>()
const networkChartRef = ref<HTMLElement>()

// 图表实例
let trendChart: echarts.ECharts | null = null
let cpuGauge: echarts.ECharts | null = null
let memoryGauge: echarts.ECharts | null = null
let diskGauge: echarts.ECharts | null = null
let networkGauge: echarts.ECharts | null = null
let networkChart: echarts.ECharts | null = null

// 初始化所有图表
const initCharts = () => {
    if (trendChartRef.value) {
        trendChart = echarts.init(trendChartRef.value)
    }
    if (cpuGaugeRef.value) {
        cpuGauge = echarts.init(cpuGaugeRef.value)
    }
    if (memoryGaugeRef.value) {
        memoryGauge = echarts.init(memoryGaugeRef.value)
    }
    if (diskGaugeRef.value) {
        diskGauge = echarts.init(diskGaugeRef.value)
    }
    if (networkGaugeRef.value) {
        networkGauge = echarts.init(networkGaugeRef.value)
    }
    if (networkChartRef.value) {
        networkChart = echarts.init(networkChartRef.value)
    }
}

// 更新所有图表
const updateAllCharts = () => {
    if (!store.currentMetrics) return

    // 更新仪表盘
    if (cpuGauge) {
        cpuGauge.setOption({
            series: [{
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                min: 0,
                max: 100,
                splitNumber: 10,
                itemStyle: {
                    color: getMetricColor(store.currentMetrics.cpu.usage)
                },
                progress: {
                    show: true,
                    width: 18
                },
                pointer: {
                    show: false
                },
                axisLine: {
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
                    show: false
                },
                detail: {
                    valueAnimation: true,
                    offsetCenter: [0, '0%'],
                    fontSize: 24,
                    formatter: '{value}%'
                },
                data: [{
                    value: store.currentMetrics.cpu.usage
                }]
            }]
        })
    }

    if (memoryGauge) {
        memoryGauge.setOption({
            series: [{
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                min: 0,
                max: 100,
                splitNumber: 10,
                itemStyle: {
                    color: getMetricColor(store.currentMetrics.memory.usage)
                },
                progress: {
                    show: true,
                    width: 18
                },
                pointer: {
                    show: false
                },
                axisLine: {
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
                    show: false
                },
                detail: {
                    valueAnimation: true,
                    offsetCenter: [0, '0%'],
                    fontSize: 24,
                    formatter: '{value}%'
                },
                data: [{
                    value: store.currentMetrics.memory.usage
                }]
            }]
        })
    }

    if (diskGauge) {
        diskGauge.setOption({
            series: [{
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                min: 0,
                max: 100,
                splitNumber: 10,
                itemStyle: {
                    color: getMetricColor(store.currentMetrics.disk.usage)
                },
                progress: {
                    show: true,
                    width: 18
                },
                pointer: {
                    show: false
                },
                axisLine: {
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
                    show: false
                },
                detail: {
                    valueAnimation: true,
                    offsetCenter: [0, '0%'],
                    fontSize: 24,
                    formatter: '{value}%'
                },
                data: [{
                    value: store.currentMetrics.disk.usage
                }]
            }]
        })
    }

    if (networkGauge) {
        const networkUsage = Math.round(
            (store.currentMetrics.network.bandwidth.in + store.currentMetrics.network.bandwidth.out) / 2
        )
        networkGauge.setOption({
            series: [{
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                min: 0,
                max: 100,
                splitNumber: 10,
                itemStyle: {
                    color: getMetricColor(networkUsage)
                },
                progress: {
                    show: true,
                    width: 18
                },
                pointer: {
                    show: false
                },
                axisLine: {
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
                    show: false
                },
                detail: {
                    valueAnimation: true,
                    offsetCenter: [0, '0%'],
                    fontSize: 24,
                    formatter: '{value}%'
                },
                data: [{
                    value: networkUsage
                }]
            }]
        })
    }
}

// 获取指标颜色
const getMetricColor = (value: number) => {
    if (value >= 90) return '#F56C6C'
    if (value >= 70) return '#E6A23C'
    return '#67C23A'
}

// 获取温度颜色
const getTemperatureColor = (celsius: number) => {
    if (celsius >= 80) return '#F56C6C'
    if (celsius >= 60) return '#E6A23C'
    return '#67C23A'
}

// CPU温度百分比
const cpuTemperaturePercentage = computed(() => {
    const temp = store.currentMetrics?.cpu.temperature || 0
    return Math.min(Math.round((temp / 100) * 100), 100)
})

// WebSocket 连接
const { isConnected, subscribe, unsubscribe } = useWebSocket({
    url: `ws://${window.location.host}/api/ws/server`
})

onMounted(() => {
    initCharts()

    // 订阅服务器状态更新
    subscribe('server_status', (data: ServerStatus) => {
        store.setStatus(data)
    })

    // 订阅服务器指标更新
    subscribe('server_metrics', (data: ServerMetrics) => {
        store.setMetrics(data)
        updateAllCharts()
    })

    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    unsubscribe('server_status')
    unsubscribe('server_metrics')
    window.removeEventListener('resize', handleResize)

    // 销毁图表实例
    trendChart?.dispose()
    cpuGauge?.dispose()
    memoryGauge?.dispose()
    diskGauge?.dispose()
    networkGauge?.dispose()
    networkChart?.dispose()
})

// 处理窗口大小变化
const handleResize = () => {
    trendChart?.resize()
    cpuGauge?.resize()
    memoryGauge?.resize()
    diskGauge?.resize()
    networkGauge?.resize()
    networkChart?.resize()
}
</script>