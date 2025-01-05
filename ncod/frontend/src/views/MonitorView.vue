<template>
    <div class="monitor">
        <el-row :gutter="20">
            <!-- CPU使用率 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>CPU使用率</span>
                            <el-button-group>
                                <el-button type="primary" link @click="refreshCPUData">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon>
                                </el-button>
                                <el-button type="primary" link @click="exportCPUData">
                                    <el-icon>
                                        <Download />
                                    </el-icon>
                                </el-button>
                            </el-button-group>
                        </div>
                    </template>
                    <div class="chart-container" ref="cpuChartRef"></div>
                </el-card>
            </el-col>

            <!-- 内存使用率 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>内存使用率</span>
                            <el-button-group>
                                <el-button type="primary" link @click="refreshMemoryData">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon>
                                </el-button>
                                <el-button type="primary" link @click="exportMemoryData">
                                    <el-icon>
                                        <Download />
                                    </el-icon>
                                </el-button>
                            </el-button-group>
                        </div>
                    </template>
                    <div class="chart-container" ref="memoryChartRef"></div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20" class="chart-row">
            <!-- 磁盘使用率 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>磁盘使用率</span>
                            <el-button-group>
                                <el-button type="primary" link @click="refreshDiskData">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon>
                                </el-button>
                                <el-button type="primary" link @click="exportDiskData">
                                    <el-icon>
                                        <Download />
                                    </el-icon>
                                </el-button>
                            </el-button-group>
                        </div>
                    </template>
                    <div class="chart-container" ref="diskChartRef"></div>
                </el-card>
            </el-col>

            <!-- 网络流量 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>网络流量</span>
                            <el-button-group>
                                <el-button type="primary" link @click="refreshNetworkData">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon>
                                </el-button>
                                <el-button type="primary" link @click="exportNetworkData">
                                    <el-icon>
                                        <Download />
                                    </el-icon>
                                </el-button>
                            </el-button-group>
                        </div>
                    </template>
                    <div class="chart-container" ref="networkChartRef"></div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20" class="chart-row">
            <!-- 系统负载 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>系统负载</span>
                            <el-button-group>
                                <el-button type="primary" link @click="refreshLoadData">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon>
                                </el-button>
                                <el-button type="primary" link @click="exportLoadData">
                                    <el-icon>
                                        <Download />
                                    </el-icon>
                                </el-button>
                            </el-button-group>
                        </div>
                    </template>
                    <div class="chart-container" ref="loadChartRef"></div>
                </el-card>
            </el-col>

            <!-- 进程状态 -->
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>进程状态</span>
                            <el-button-group>
                                <el-button type="primary" link @click="refreshProcessData">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon>
                                </el-button>
                                <el-button type="primary" link @click="exportProcessData">
                                    <el-icon>
                                        <Download />
                                    </el-icon>
                                </el-button>
                            </el-button-group>
                        </div>
                    </template>
                    <div class="chart-container" ref="processChartRef"></div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 系统日志 -->
        <el-row :gutter="20" class="table-row">
            <el-col :span="24">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>系统日志</span>
                            <div class="header-right">
                                <el-input v-model="searchKeyword" placeholder="搜索日志..." style="width: 200px" clearable>
                                    <template #prefix>
                                        <el-icon>
                                            <Search />
                                        </el-icon>
                                    </template>
                                </el-input>
                                <el-select v-model="logLevel" placeholder="日志级别" clearable>
                                    <el-option v-for="level in logLevels" :key="level.value" :label="level.label"
                                        :value="level.value" />
                                </el-select>
                                <el-button type="primary" @click="exportLogs">
                                    <el-icon>
                                        <Download />
                                    </el-icon>导出日志
                                </el-button>
                            </div>
                        </div>
                    </template>
                    <el-table :data="filteredLogs" style="width: 100%" v-loading="loading">
                        <el-table-column prop="timestamp" label="时间" width="180" />
                        <el-table-column prop="level" label="级别" width="100">
                            <template #default="{ row }">
                                <el-tag :type="getLogLevelType(row.level)">
                                    {{ row.level }}
                                </el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column prop="source" label="来源" width="150" />
                        <el-table-column prop="message" label="内容" />
                    </el-table>
                    <div class="pagination">
                        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
                            :page-sizes="[10, 20, 50, 100]" :total="total"
                            layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange"
                            @current-change="handleCurrentChange" />
                    </div>
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Refresh, Download, Search } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 图表引用
const cpuChartRef = ref<HTMLElement>()
const memoryChartRef = ref<HTMLElement>()
const diskChartRef = ref<HTMLElement>()
const networkChartRef = ref<HTMLElement>()
const loadChartRef = ref<HTMLElement>()
const processChartRef = ref<HTMLElement>()

// 日志相关
const searchKeyword = ref('')
const logLevel = ref('')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(100)

const logLevels = [
    { value: 'info', label: '信息' },
    { value: 'warning', label: '警告' },
    { value: 'error', label: '错误' },
    { value: 'debug', label: '调试' }
]

// 模拟日志数据
const logs = ref([
    {
        timestamp: '2024-01-20 10:30:45',
        level: 'info',
        source: 'System',
        message: '系统启动成功'
    },
    {
        timestamp: '2024-01-20 10:31:22',
        level: 'warning',
        source: 'Memory',
        message: '内存使用率超过80%'
    },
    {
        timestamp: '2024-01-20 10:32:15',
        level: 'error',
        source: 'Disk',
        message: '磁盘空间不足'
    }
])

// 过滤日志
const filteredLogs = computed(() => {
    return logs.value.filter(log => {
        const matchKeyword = !searchKeyword.value ||
            log.message.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
            log.source.toLowerCase().includes(searchKeyword.value.toLowerCase())

        const matchLevel = !logLevel.value || log.level === logLevel.value

        return matchKeyword && matchLevel
    })
})

// 初始化图表
onMounted(() => {
    // CPU使用率图表
    if (cpuChartRef.value) {
        const cpuChart = echarts.init(cpuChartRef.value)
        cpuChart.setOption({
            tooltip: {
                trigger: 'axis'
            },
            xAxis: {
                type: 'category',
                data: ['12:00', '12:05', '12:10', '12:15', '12:20', '12:25', '12:30']
            },
            yAxis: {
                type: 'value',
                max: 100,
                axisLabel: {
                    formatter: '{value}%'
                }
            },
            series: [
                {
                    name: 'CPU使用率',
                    type: 'line',
                    data: [30, 45, 62, 58, 75, 65, 50],
                    areaStyle: {},
                    itemStyle: {
                        color: '#409EFF'
                    }
                }
            ]
        })
    }

    // 内存使用率图表
    if (memoryChartRef.value) {
        const memoryChart = echarts.init(memoryChartRef.value)
        memoryChart.setOption({
            tooltip: {
                trigger: 'axis'
            },
            xAxis: {
                type: 'category',
                data: ['12:00', '12:05', '12:10', '12:15', '12:20', '12:25', '12:30']
            },
            yAxis: {
                type: 'value',
                max: 100,
                axisLabel: {
                    formatter: '{value}%'
                }
            },
            series: [
                {
                    name: '内存使用率',
                    type: 'line',
                    data: [45, 52, 58, 65, 72, 68, 75],
                    areaStyle: {},
                    itemStyle: {
                        color: '#67C23A'
                    }
                }
            ]
        })
    }

    // 磁盘使用率图表
    if (diskChartRef.value) {
        const diskChart = echarts.init(diskChartRef.value)
        diskChart.setOption({
            tooltip: {
                trigger: 'item'
            },
            legend: {
                orient: 'vertical',
                left: 'left'
            },
            series: [
                {
                    name: '磁盘使用情况',
                    type: 'pie',
                    radius: '50%',
                    data: [
                        { value: 75, name: '已使用', itemStyle: { color: '#F56C6C' } },
                        { value: 25, name: '可用', itemStyle: { color: '#67C23A' } }
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
        })
    }

    // 网络流量图表
    if (networkChartRef.value) {
        const networkChart = echarts.init(networkChartRef.value)
        networkChart.setOption({
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['上传', '下载']
            },
            xAxis: {
                type: 'category',
                data: ['12:00', '12:05', '12:10', '12:15', '12:20', '12:25', '12:30']
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    formatter: '{value} MB/s'
                }
            },
            series: [
                {
                    name: '上传',
                    type: 'line',
                    data: [2.5, 3.2, 4.1, 3.8, 4.5, 3.9, 4.2],
                    itemStyle: {
                        color: '#E6A23C'
                    }
                },
                {
                    name: '下载',
                    type: 'line',
                    data: [5.2, 6.8, 7.5, 6.9, 8.2, 7.5, 6.8],
                    itemStyle: {
                        color: '#409EFF'
                    }
                }
            ]
        })
    }

    // 系统负载图表
    if (loadChartRef.value) {
        const loadChart = echarts.init(loadChartRef.value)
        loadChart.setOption({
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['1分钟', '5分钟', '15分钟']
            },
            xAxis: {
                type: 'category',
                data: ['12:00', '12:05', '12:10', '12:15', '12:20', '12:25', '12:30']
            },
            yAxis: {
                type: 'value'
            },
            series: [
                {
                    name: '1分钟',
                    type: 'line',
                    data: [1.2, 1.5, 1.8, 1.6, 2.1, 1.9, 1.7],
                    itemStyle: {
                        color: '#409EFF'
                    }
                },
                {
                    name: '5分钟',
                    type: 'line',
                    data: [1.5, 1.7, 1.9, 1.8, 2.0, 1.8, 1.6],
                    itemStyle: {
                        color: '#67C23A'
                    }
                },
                {
                    name: '15分钟',
                    type: 'line',
                    data: [1.6, 1.8, 1.7, 1.9, 1.8, 1.7, 1.5],
                    itemStyle: {
                        color: '#E6A23C'
                    }
                }
            ]
        })
    }

    // 进程状态图表
    if (processChartRef.value) {
        const processChart = echarts.init(processChartRef.value)
        processChart.setOption({
            tooltip: {
                trigger: 'item'
            },
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
        })
    }
})

// 刷新数据方法
const refreshCPUData = () => {
    // 实现刷新CPU数据的逻辑
}

const refreshMemoryData = () => {
    // 实现刷新内存数据的逻辑
}

const refreshDiskData = () => {
    // 实现刷新磁盘数据的逻辑
}

const refreshNetworkData = () => {
    // 实现刷新网络数据的逻辑
}

const refreshLoadData = () => {
    // 实现刷新负载数据的逻辑
}

const refreshProcessData = () => {
    // 实现刷新进程数据的逻辑
}

// 导出数据方法
const exportCPUData = () => {
    // 实现导出CPU数据的逻辑
}

const exportMemoryData = () => {
    // 实现导出内存数据的逻辑
}

const exportDiskData = () => {
    // 实现导出磁盘数据的逻辑
}

const exportNetworkData = () => {
    // 实现导出网络数据的逻辑
}

const exportLoadData = () => {
    // 实现导出负载数据的逻辑
}

const exportProcessData = () => {
    // 实现导出进程数据的逻辑
}

const exportLogs = () => {
    // 实现导出日志的逻辑
}

// 分页方法
const handleSizeChange = (val: number) => {
    pageSize.value = val
    // 重新加载数据
}

const handleCurrentChange = (val: number) => {
    currentPage.value = val
    // 重新加载数据
}

// 获取日志级别样式
const getLogLevelType = (level: string) => {
    const typeMap: Record<string, string> = {
        info: 'info',
        warning: 'warning',
        error: 'danger',
        debug: ''
    }
    return typeMap[level] || ''
}
</script>

<style scoped>
.monitor {
    padding: 20px;
}

.chart-row {
    margin-top: 20px;
}

.table-row {
    margin-top: 20px;
}

.chart-container {
    height: 300px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-right {
    display: flex;
    gap: 10px;
    align-items: center;
}

.pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}
</style>