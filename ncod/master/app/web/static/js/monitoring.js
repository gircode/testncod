// 全局变量
let charts = {};
let currentView = 'dashboard';

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 注册视图切换事件
    document.querySelectorAll('[data-view]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(e.target.dataset.view);
        });
    });

    // 注册时间范围变更事件
    document.getElementById('time-range').addEventListener('change', refreshDashboard);

    // 注册图表类型变更事件
    document.querySelectorAll('[id^="chart-"]').forEach(checkbox => {
        checkbox.addEventListener('change', refreshDashboard);
    });

    // 注册按钮事件
    document.getElementById('export-metrics').addEventListener('click', exportMetrics);
    document.getElementById('import-metrics').addEventListener('click', importMetrics);
    document.getElementById('add-rule').addEventListener('click', showAddRuleModal);
    document.getElementById('save-rule').addEventListener('click', saveAlertRule);
    document.getElementById('save-config').addEventListener('click', saveConfig);
    document.getElementById('reload-config').addEventListener('click', reloadConfig);

    // 初始化仪表板
    refreshDashboard();
    // 启动自动刷新
    setInterval(refreshDashboard, 60000); // 每分钟刷新一次
});

// 视图切换
function switchView(view) {
    document.querySelectorAll('.view').forEach(el => el.style.display = 'none');
    document.getElementById(`${view}-view`).style.display = 'block';
    currentView = view;

    // 加载视图数据
    switch (view) {
        case 'dashboard':
            refreshDashboard();
            break;
        case 'metrics':
            loadMetrics();
            break;
        case 'alerts':
            loadAlertRules();
            break;
        case 'config':
            loadConfig();
            break;
    }
}

// 刷新仪表板
async function refreshDashboard() {
    const timeRange = document.getElementById('time-range').value;
    const enabledCharts = Array.from(document.querySelectorAll('[id^="chart-"]:checked'))
        .map(cb => cb.value);

    try {
        // 清除旧图表
        Object.values(charts).forEach(chart => chart.destroy());
        charts = {};

        // 获取数据
        const response = await fetch(`/api/metrics/dashboard?time_range=${timeRange}`);
        const data = await response.json();

        // 创建图��
        const container = document.getElementById('charts-container');
        container.innerHTML = '';

        if (enabledCharts.includes('system')) {
            await createSystemMetricsCharts(container, data.system_metrics);
        }
        if (enabledCharts.includes('performance')) {
            await createPerformanceMetricsCharts(container, data.performance_metrics);
        }
        if (enabledCharts.includes('error')) {
            await createErrorMetricsCharts(container, data.error_metrics);
        }
    } catch (error) {
        showError('刷新仪表板失败', error);
    }
}

// 创建系统指标图表
function createSystemMetricsCharts(container, data) {
    // CPU使用率
    const cpuCanvas = createChartCanvas(container, 'cpu-chart');
    charts.cpu = new Chart(cpuCanvas, {
        type: 'line',
        data: {
            labels: data.cpu_usage.timestamps,
            datasets: [{
                label: 'CPU使用率',
                data: data.cpu_usage.values,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'CPU使用率'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // 内存使用率
    const memoryCanvas = createChartCanvas(container, 'memory-chart');
    charts.memory = new Chart(memoryCanvas, {
        type: 'line',
        data: {
            labels: data.memory_usage.timestamps,
            datasets: [{
                label: '已用内存',
                data: data.memory_usage.used,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                fill: true
            }, {
                label: '可用内存',
                data: data.memory_usage.available,
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '内存使用情况'
                }
            },
            scales: {
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });

    // 磁盘使用率
    const diskCanvas = createChartCanvas(container, 'disk-chart');
    charts.disk = new Chart(diskCanvas, {
        type: 'doughnut',
        data: {
            labels: ['已用空间', '可用空间'],
            datasets: [{
                data: [data.disk_usage.used, data.disk_usage.available],
                backgroundColor: [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '磁盘使用情况'
                }
            }
        }
    });

    // 网络流量
    const networkCanvas = createChartCanvas(container, 'network-chart');
    charts.network = new Chart(networkCanvas, {
        type: 'line',
        data: {
            labels: data.network_traffic.timestamps,
            datasets: [{
                label: '发送',
                data: data.network_traffic.sent,
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }, {
                label: '接收',
                data: data.network_traffic.received,
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '网络流量'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 创建性能指标图表
function createPerformanceMetricsCharts(container, data) {
    // 响应时间分布
    const responseTimeCanvas = createChartCanvas(container, 'response-time-chart');
    charts.responseTime = new Chart(responseTimeCanvas, {
        type: 'violin',
        data: {
            labels: data.response_times.labels,
            datasets: [{
                data: data.response_times.values,
                backgroundColor: 'rgba(75, 192, 192, 0.5)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '响应时间分布'
                }
            }
        }
    });

    // 请求数量趋势
    const requestCountCanvas = createChartCanvas(container, 'request-count-chart');
    charts.requestCount = new Chart(requestCountCanvas, {
        type: 'bar',
        data: {
            labels: data.request_counts.timestamps,
            datasets: [{
                label: '请求��量',
                data: data.request_counts.values,
                backgroundColor: 'rgba(54, 162, 235, 0.5)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '请求数量趋势'
                }
            }
        }
    });
}

// 创建错误指标图表
function createErrorMetricsCharts(container, data) {
    // 错误类型分布
    const errorTypeCanvas = createChartCanvas(container, 'error-type-chart');
    charts.errorType = new Chart(errorTypeCanvas, {
        type: 'pie',
        data: {
            labels: data.error_types.labels,
            datasets: [{
                data: data.error_types.values,
                backgroundColor: [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 205, 86)',
                    'rgb(75, 192, 192)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '错误类型分布'
                }
            }
        }
    });

    // 错误趋势
    const errorTrendCanvas = createChartCanvas(container, 'error-trend-chart');
    charts.errorTrend = new Chart(errorTrendCanvas, {
        type: 'line',
        data: {
            labels: data.error_trend.timestamps,
            datasets: [{
                label: '错误数量',
                data: data.error_trend.values,
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '错误趋势'
                }
            }
        }
    });
}

// 加载指标数据
async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        
        const tbody = document.getElementById('metrics-table');
        tbody.innerHTML = '';
        
        data.forEach(metric => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${metric.name}</td>
                <td>${metric.type}</td>
                <td>${metric.value}</td>
                <td>${formatDateTime(metric.timestamp)}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="showMetricDetails('${metric.name}')">
                        <i class="fas fa-chart-line"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        showError('加载指标数据失败', error);
    }
}

// 加载警报规则
async function loadAlertRules() {
    try {
        const response = await fetch('/api/alerts/rules');
        const data = await response.json();
        
        const container = document.getElementById('alert-rules');
        container.innerHTML = '';
        
        data.forEach(rule => {
            const div = document.createElement('div');
            div.className = 'alert-rule';
            div.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${rule.name}</h6>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-warning" onclick="editRule('${rule.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteRule('${rule.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="mt-2">
                    <small class="text-muted">
                        ${rule.metric_type} ${rule.condition} ${rule.threshold}
                        (${rule.severity})
                    </small>
                </div>
            `;
            container.appendChild(div);
        });
        
        // 加载活动警报
        await loadActiveAlerts();
    } catch (error) {
        showError('加载警报规则失败', error);
    }
}

// 加载活动警报
async function loadActiveAlerts() {
    try {
        const response = await fetch('/api/alerts/active');
        const data = await response.json();
        
        const container = document.getElementById('active-alerts');
        container.innerHTML = '';
        
        data.forEach(alert => {
            const div = document.createElement('div');
            div.className = `alert alert-${getSeverityClass(alert.severity)}`;
            div.innerHTML = `
                <h6 class="alert-heading">${alert.rule_name}</h6>
                <p class="mb-0">${alert.message}</p>
                <small class="text-muted">${formatDateTime(alert.timestamp)}</small>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        showError('加载活动警报失败', error);
    }
}

// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        document.getElementById('monitoring-config').value = JSON.stringify(data.monitoring, null, 2);
        document.getElementById('alert-config').value = JSON.stringify(data.alerts, null, 2);
    } catch (error) {
        showError('加载配置失败', error);
    }
}

// 保存配置
async function saveConfig() {
    try {
        const monitoringConfig = JSON.parse(document.getElementById('monitoring-config').value);
        const alertConfig = JSON.parse(document.getElementById('alert-config').value);
        
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                monitoring: monitoringConfig,
                alerts: alertConfig
            })
        });
        
        if (response.ok) {
            showSuccess('配置已保存');
        } else {
            throw new Error('保存配置失败');
        }
    } catch (error) {
        showError('保存配置失败', error);
    }
}

// 重新加载配置
async function reloadConfig() {
    try {
        const response = await fetch('/api/config/reload', {
            method: 'POST'
        });
        
        if (response.ok) {
            showSuccess('配置已重新加载');
            await loadConfig();
        } else {
            throw new Error('重新加载配置失败');
        }
    } catch (error) {
        showError('重新加载配置失败', error);
    }
}

// 导出指标数据
async function exportMetrics() {
    try {
        const response = await fetch('/api/metrics/export');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `metrics_${formatDate(new Date())}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        showError('导出指标数据失败', error);
    }
}

// 导入指标数据
function importMetrics() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
        try {
            const file = e.target.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/metrics/import', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                showSuccess('指标数据已导入');
                await loadMetrics();
            } else {
                throw new Error('导入指标数据失败');
            }
        } catch (error) {
            showError('导入指标数据失败', error);
        }
    };
    input.click();
}

// 显示警报规则模态框
function showAddRuleModal() {
    const modal = new bootstrap.Modal(document.getElementById('alert-rule-modal'));
    document.getElementById('alert-rule-form').reset();
    modal.show();
}

// 保存警报规则
async function saveAlertRule() {
    try {
        const form = document.getElementById('alert-rule-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        const response = await fetch('/api/alerts/rules', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('alert-rule-modal'));
            modal.hide();
            showSuccess('警报规则已保存');
            await loadAlertRules();
        } else {
            throw new Error('保存警报规则失败');
        }
    } catch (error) {
        showError('保存警报规则失败', error);
    }
}

// 编辑警报规则
async function editRule(ruleId) {
    try {
        const response = await fetch(`/api/alerts/rules/${ruleId}`);
        const rule = await response.json();
        
        const form = document.getElementById('alert-rule-form');
        Object.entries(rule).forEach(([key, value]) => {
            const input = form.elements[key];
            if (input) {
                input.value = value;
            }
        });
        
        const modal = new bootstrap.Modal(document.getElementById('alert-rule-modal'));
        modal.show();
    } catch (error) {
        showError('加载警报规则失败', error);
    }
}

// 删除警报规则
async function deleteRule(ruleId) {
    if (confirm('确定要删除这条警报规则吗？')) {
        try {
            const response = await fetch(`/api/alerts/rules/${ruleId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showSuccess('警报规则已删除');
                await loadAlertRules();
            } else {
                throw new Error('删除警报规则失败');
            }
        } catch (error) {
            showError('删除警报规则失败', error);
        }
    }
}

// 显示指标详情
function showMetricDetails(metricName) {
    // TODO: 实现指标详情展示
}

// 工具函数
function createChartCanvas(container, id) {
    const div = document.createElement('div');
    div.className = 'chart-container';
    const canvas = document.createElement('canvas');
    canvas.id = id;
    div.appendChild(canvas);
    container.appendChild(div);
    return canvas;
}

function formatDateTime(timestamp) {
    return moment(timestamp).format('YYYY-MM-DD HH:mm:ss');
}

function formatDate(date) {
    return moment(date).format('YYYYMMDD');
}

function getSeverityClass(severity) {
    switch (severity) {
        case 'critical':
            return 'danger';
        case 'error':
            return 'warning';
        case 'warning':
            return 'info';
        default:
            return 'secondary';
    }
}

function showSuccess(message) {
    // TODO: 实现成功提示
    console.log('Success:', message);
}

function showError(message, error) {
    // TODO: 实现错误提示
    console.error(message, error);
} 