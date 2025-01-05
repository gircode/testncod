<template>
    <div class="home">
        <el-row :gutter="20">
            <el-col :span="6">
                <el-card shadow="hover" class="stat-card">
                    <template #header>
                        <div class="card-header">
                            <span>总设备数</span>
                        </div>
                    </template>
                    <div class="card-content">
                        <el-statistic :value="deviceCount" title="台">
                            <template #prefix>
                                <el-icon>
                                    <Monitor />
                                </el-icon>
                            </template>
                        </el-statistic>
                    </div>
                </el-card>
            </el-col>

            <el-col :span="6">
                <el-card shadow="hover" class="stat-card">
                    <template #header>
                        <div class="card-header">
                            <span>在线设备</span>
                        </div>
                    </template>
                    <div class="card-content">
                        <el-statistic :value="onlineDevices" title="台">
                            <template #prefix>
                                <el-icon>
                                    <Connection />
                                </el-icon>
                            </template>
                        </el-statistic>
                    </div>
                </el-card>
            </el-col>

            <el-col :span="6">
                <el-card shadow="hover" class="stat-card">
                    <template #header>
                        <div class="card-header">
                            <span>告警设备</span>
                        </div>
                    </template>
                    <div class="card-content">
                        <el-statistic :value="warningDevices" title="台" value-style="color: #E6A23C">
                            <template #prefix>
                                <el-icon>
                                    <Warning />
                                </el-icon>
                            </template>
                        </el-statistic>
                    </div>
                </el-card>
            </el-col>

            <el-col :span="6">
                <el-card shadow="hover" class="stat-card">
                    <template #header>
                        <div class="card-header">
                            <span>故障设备</span>
                        </div>
                    </template>
                    <div class="card-content">
                        <el-statistic :value="errorDevices" title="台" value-style="color: #F56C6C">
                            <template #prefix>
                                <el-icon>
                                    <CircleClose />
                                </el-icon>
                            </template>
                        </el-statistic>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20" class="chart-row">
            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>设备状态分布</span>
                        </div>
                    </template>
                    <div class="chart-container" ref="pieChartRef"></div>
                </el-card>
            </el-col>

            <el-col :span="12">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>近7天告警趋势</span>
                        </div>
                    </template>
                    <div class="chart-container" ref="lineChartRef"></div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="20" class="table-row">
            <el-col :span="24">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>最近告警</span>
                            <el-button type="primary" link>查看更多</el-button>
                        </div>
                    </template>
                    <el-table :data="recentAlerts" style="width: 100%">
                        <el-table-column prop="time" label="时间" width="180" />
                        <el-table-column prop="device" label="设备" width="180" />
                        <el-table-column prop="type" label="类型" width="120">
                            <template #default="{ row }">
                                <el-tag :type="row.type === 'warning' ? 'warning' : 'danger'">
                                    {{ row.type === 'warning' ? '警告' : '错误' }}
                                </el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column prop="message" label="告警信息" />
                        <el-table-column prop="status" label="状态" width="120">
                            <template #default="{ row }">
                                <el-tag :type="row.status === 'pending' ? 'info' : 'success'">
                                    {{ row.status === 'pending' ? '待处理' : '已处理' }}
                                </el-tag>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Monitor, Connection, Warning, CircleClose } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 模拟数据
const deviceCount = ref(128)
const onlineDevices = ref(98)
const warningDevices = ref(15)
const errorDevices = ref(5)

const recentAlerts = ref([
    {
        time: '2024-01-20 10:30:45',
        device: 'Server-001',
        type: 'warning',
        message: 'CPU使用率超过80%',
        status: 'pending'
    },
    {
        time: '2024-01-20 09:15:22',
        device: 'Server-002',
        type: 'error',
        message: '磁盘空间不足',
        status: 'resolved'
    },
    {
        time: '2024-01-20 08:45:10',
        device: 'Server-003',
        type: 'warning',
        message: '内存使用率过高',
        status: 'pending'
    }
])

const pieChartRef = ref<HTMLElement>()
const lineChartRef = ref<HTMLElement>()

onMounted(() => {
    // 初始化饼图
    if (pieChartRef.value) {
        const pieChart = echarts.init(pieChartRef.value)
        pieChart.setOption({
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
                        { value: onlineDevices.value, name: '在线', itemStyle: { color: '#67C23A' } },
                        { value: warningDevices.value, name: '警告', itemStyle: { color: '#E6A23C' } },
                        { value: errorDevices.value, name: '故障', itemStyle: { color: '#F56C6C' } },
                        { value: deviceCount.value - onlineDevices.value - warningDevices.value - errorDevices.value, name: '离线', itemStyle: { color: '#909399' } }
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

    // 初始化折线图
    if (lineChartRef.value) {
        const lineChart = echarts.init(lineChartRef.value)
        lineChart.setOption({
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['警告', '错误']
            },
            xAxis: {
                type: 'category',
                data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            },
            yAxis: {
                type: 'value'
            },
            series: [
                {
                    name: '警告',
                    type: 'line',
                    data: [5, 8, 3, 9, 6, 4, 7],
                    itemStyle: { color: '#E6A23C' }
                },
                {
                    name: '错误',
                    type: 'line',
                    data: [2, 1, 3, 2, 1, 2, 1],
                    itemStyle: { color: '#F56C6C' }
                }
            ]
        })
    }
})
</script>

<style scoped>
.home {
    padding: 20px;
}

.stat-card {
    height: 100%;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-content {
    text-align: center;
}

.chart-row {
    margin-top: 20px;
}

.chart-container {
    height: 300px;
}

.table-row {
    margin-top: 20px;
}

:deep(.el-card__header) {
    padding: 12px 20px;
    border-bottom: 1px solid #ebeef5;
    box-sizing: border-box;
}
</style>