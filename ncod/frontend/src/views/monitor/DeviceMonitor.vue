<template>
    <div class="device-monitor">
        <!-- 设备状态卡片 -->
        <a-card class="status-card">
            <template #title>设备状态</template>
            <a-row :gutter="16">
                <a-col :span="6" v-for="metric in metrics" :key="metric.type">
                    <a-statistic :title="metric.name" :value="metric.value" :precision="2" :suffix="metric.unit"
                        :value-style="getValueStyle(metric.value, metric.threshold)" />
                </a-col>
            </a-row>
        </a-card>

        <!-- 指标趋势图 -->
        <a-card class="chart-card">
            <template #title>性能趋势</template>
            <template #extra>
                <a-space>
                    <a-select v-model:value="selectedMetric" style="width: 120px">
                        <a-select-option v-for="type in METRIC_TYPES" :key="type.value" :value="type.value">
                            {{ type.label }}
                        </a-select-option>
                    </a-select>
                    <a-range-picker v-model:value="timeRange" :show-time="true" @change="handleTimeRangeChange" />
                </a-space>
            </template>
            <div ref="chartRef" style="height: 400px"></div>
        </a-card>

        <!-- 告警列表 -->
        <a-card class="alert-card">
            <template #title>告警信息</template>
            <a-table :columns="alertColumns" :data-source="alerts" :loading="loading" row-key="id">
                <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'level'">
                        <a-tag :color="getAlertColor(record.level)">
                            {{ record.level }}
                        </a-tag>
                    </template>
                    <template v-if="column.key === 'created_at'">
                        {{ formatDateTime(record.created_at) }}
                    </template>
                </template>
            </a-table>
        </a-card>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import * as echarts from 'echarts';
import { deviceStatsApi } from '@/api/device-stats';
import { METRIC_TYPES } from '@/api/alert-rule';
import { formatDateTime } from '@/utils/date';

interface MetricData {
    type: string;
    name: string;
    value: number;
    unit: string;
    threshold?: number;
}

interface TimeRange {
    start: Date;
    end: Date;
}

interface ChartData {
    time: string;
    value: number;
}

interface AlertLevel {
    critical: string;
    major: string;
    minor: string;
    info: string;
}

interface DeviceHistory {
    time: string;
    value: number;
}

// 告警列定义
const alertColumns = [
    { title: '时间', dataIndex: 'created_at', key: 'created_at' },
    { title: '级别', dataIndex: 'level', key: 'level' },
    { title: '指标', dataIndex: 'metric_type', key: 'metric_type' },
    { title: '描述', dataIndex: 'description', key: 'description' }
];

interface Alert {
    id: string;
    level: string;
    metric_type: string;
    description: string;
    created_at: string;
}

export default defineComponent({
    name: 'DeviceMonitor',
    setup() {
        const route = useRoute();
        const deviceId = route.params.id as string;
        const loading = ref(false);
        const chartRef = ref<HTMLElement>();
        const metrics = ref<MetricData[]>([]);
        const timeRange = ref<TimeRange>({
            start: new Date(Date.now() - 24 * 60 * 60 * 1000),
            end: new Date()
        });

        const chart = ref<echarts.ECharts>();
        const selectedMetric = ref(METRIC_TYPES[0].value);

        const alerts = ref<Alert[]>([]);

        // 加载实时指标
        const loadMetrics = async () => {
            try {
                loading.value = true;
                const res = await deviceStatsApi.getDeviceStats(deviceId);
                metrics.value = res.data.map((stat: any) => ({
                    type: stat.type,
                    name: METRIC_TYPES.find(t => t.value === stat.type)?.label || stat.type,
                    value: stat.value,
                    unit: METRIC_TYPES.find(t => t.value === stat.type)?.unit || '',
                    threshold: stat.threshold
                }));
            } catch (error) {
                if (error instanceof Error) {
                    message.error(error.message);
                } else {
                    message.error('加载指标失败');
                }
            } finally {
                loading.value = false;
            }
        };

        // 加载历史数据
        const loadHistoryData = async () => {
            try {
                const res = await deviceStatsApi.getDeviceHistory(
                    deviceId,
                    timeRange.value.start.toISOString(),
                    timeRange.value.end.toISOString()
                );
                return res.data.map((item: any) => ({
                    time: formatDateTime(item.time),
                    value: item.value
                }));
            } catch (error) {
                if (error instanceof Error) {
                    message.error(error.message);
                } else {
                    message.error('加载历史数据失败');
                }
                return [];
            }
        };

        // 处理时间范围变更
        const handleTimeRangeChange = async (dates: [Date, Date]) => {
            timeRange.value = {
                start: dates[0],
                end: dates[1]
            };
            await updateChart();
        };

        // 初始化图表
        const initChart = () => {
            if (!chartRef.value) return;
            chart.value = echarts.init(chartRef.value);

            // 窗口大小变化时自动调整图表大小
            window.addEventListener('resize', () => {
                chart.value?.resize();
            });
        };

        // 加载告警信息
        const loadAlerts = async () => {
            try {
                const res = await deviceStatsApi.getDeviceAlerts(deviceId, {
                    start_time: timeRange.value.start.toISOString(),
                    end_time: timeRange.value.end.toISOString()
                });
                alerts.value = res.data;
            } catch (error) {
                if (error instanceof Error) {
                    message.error(error.message);
                } else {
                    message.error('加载告警失败');
                }
            }
        };

        // 更新图表
        const updateChart = async () => {
            if (!chart.value) return;

            try {
                const data = await loadHistoryData();
                const metric = METRIC_TYPES.find(m => m.value === selectedMetric.value);
                const thresholds = metrics.value.find(m => m.type === selectedMetric.value)?.threshold;

                chart.value.setOption({
                    title: {
                        text: metric?.label || '性能趋势'
                    },
                    tooltip: {
                        trigger: 'axis',
                        formatter: (params: any) => {
                            const p = params[0];
                            return `${p.name}<br/>${p.value}${metric?.unit || ''}`;
                        }
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
                        data: data.map(item => item.time)
                    },
                    yAxis: {
                        type: 'value',
                        name: metric?.unit || '',
                        axisLabel: {
                            formatter: `{value}${metric?.unit || ''}`
                        }
                    },
                    series: [{
                        name: metric?.label || '',
                        type: 'line',
                        data: data.map((item: DeviceHistory) => item.value),
                        smooth: true,
                        markLine: thresholds ? {
                            data: [
                                {
                                    name: '阈值',
                                    yAxis: thresholds,
                                    lineStyle: { color: '#ff4d4f' }
                                }
                            ]
                        } : undefined
                    }]
                });
            } catch (error) {
                console.error('更新图表失败:', error);
            }
        };

        // 监听指标和时间范围变化
        watch([selectedMetric, timeRange], () => {
            updateChart();
            loadAlerts();
        });

        // 获取值的样式
        const getValueStyle = (value: number, threshold?: number) => {
            if (!threshold) return {};
            return {
                color: value >= threshold * 0.9 ? '#cf1322' :
                    value >= threshold * 0.8 ? '#fa8c16' :
                        value >= threshold * 0.7 ? '#faad14' : '#3f8600'
            };
        };

        // 获取告警级别颜色
        const alertLevels: AlertLevel = {
            critical: 'red',
            major: 'orange',
            minor: 'yellow',
            info: 'blue'
        };

        const getAlertColor = (value: number, threshold?: number): string => {
            if (!threshold) return alertLevels.info;
            if (value >= threshold * 0.9) return alertLevels.critical;
            if (value >= threshold * 0.8) return alertLevels.major;
            if (value >= threshold * 0.7) return alertLevels.minor;
            return alertLevels.info;
        };

        onMounted(() => {
            loadMetrics();
            initChart();
            updateChart();
            loadAlerts();

            // 定时刷新数据
            const timer = setInterval(() => {
                loadMetrics();
                loadAlerts();
            }, 30000);

            return () => {
                clearInterval(timer);
                chart.value?.dispose();
            };
        });

        return {
            loading,
            metrics,
            chartRef,
            timeRange,
            handleTimeRangeChange,
            getAlertColor,
            formatDateTime,
            selectedMetric,
            METRIC_TYPES,
            getValueStyle,
            alerts,
            alertColumns
        };
    }
});
</script>

<style lang="less" scoped>
.device-monitor {
    padding: 24px;

    .ant-card {
        margin-bottom: 24px;
    }

    .status-card {
        .ant-statistic {
            text-align: center;
        }
    }

    .chart-card {
        .echarts {
            height: 400px;
        }
    }
}
</style>