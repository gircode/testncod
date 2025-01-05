// 节点状态监控
class NodeMonitor {
    constructor() {
        this.nodes = new Map();
        this.filters = {
            status: 'all',
            type: 'all'
        };
        this.init();
    }

    init() {
        this.loadNodes();
        this.setupFilters();
        this.setupRefreshInterval();
    }

    async loadNodes() {
        try {
            const response = await fetch('/api/monitor/nodes');
            const data = await response.json();
            this.updateNodesGrid(data);
        } catch (error) {
            console.error('Failed to load nodes:', error);
            showError('加载节点数据失败');
        }
    }

    updateNodesGrid(nodes) {
        const grid = document.querySelector('.nodes-grid');
        if (!grid) return;

        grid.innerHTML = nodes.map(node => this.renderNodeCard(node)).join('');
    }

    renderNodeCard(node) {
        return `
            <div class="node-card ${node.status}" data-id="${node.id}">
                <div class="node-header">
                    <h3>${node.name}</h3>
                    <span class="node-type">${node.type}</span>
                </div>
                <div class="node-stats">
                    <div class="stat">
                        <span class="label">CPU</span>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${node.cpu_usage}%">
                                ${node.cpu_usage}%
                            </div>
                        </div>
                    </div>
                    <div class="stat">
                        <span class="label">内存</span>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${node.memory_usage}%">
                                ${node.memory_usage}%
                            </div>
                        </div>
                    </div>
                    <div class="stat">
                        <span class="label">磁盘</span>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${node.disk_usage}%">
                                ${node.disk_usage}%
                            </div>
                        </div>
                    </div>
                </div>
                <div class="node-info">
                    <p>IP: ${node.ip}</p>
                    <p>端口: ${node.port}</p>
                    <p>最后心跳: ${formatTime(node.last_heartbeat)}</p>
                </div>
                <div class="node-actions">
                    <button onclick="nodeMonitor.showNodeDetails('${node.id}')" class="btn-info">详情</button>
                    <button onclick="nodeMonitor.restartNode('${node.id}')" class="btn-warning">重启</button>
                    ${node.status === 'error' ? 
                        `<button onclick="nodeMonitor.troubleshootNode('${node.id}')" class="btn-danger">诊断</button>` 
                        : ''}
                </div>
            </div>
        `;
    }

    setupFilters() {
        const filterForm = document.getElementById('nodeFilters');
        if (filterForm) {
            filterForm.addEventListener('change', (e) => {
                this.filters[e.target.name] = e.target.value;
                this.applyFilters();
            });
        }
    }

    applyFilters() {
        const nodes = document.querySelectorAll('.node-card');
        nodes.forEach(node => {
            const status = node.classList.contains(this.filters.status);
            const type = node.querySelector('.node-type').textContent === this.filters.type;
            
            const visible = (this.filters.status === 'all' || status) && 
                          (this.filters.type === 'all' || type);
            
            node.style.display = visible ? '' : 'none';
        });
    }

    setupRefreshInterval() {
        setInterval(() => this.loadNodes(), 30000); // 每30秒刷新一次
    }

    async showNodeDetails(nodeId) {
        try {
            const response = await fetch(`/api/monitor/nodes/${nodeId}/details`);
            const data = await response.json();
            
            showModal({
                title: '节点详情',
                content: this.renderNodeDetails(data),
                width: '800px'
            });
        } catch (error) {
            console.error('Failed to load node details:', error);
            showError('加载节点详情失败');
        }
    }

    renderNodeDetails(node) {
        return `
            <div class="node-details">
                <div class="detail-section">
                    <h4>基本信息</h4>
                    <table class="detail-table">
                        <tr>
                            <td>节点ID:</td>
                            <td>${node.id}</td>
                        </tr>
                        <tr>
                            <td>节点名称:</td>
                            <td>${node.name}</td>
                        </tr>
                        <tr>
                            <td>节点类型:</td>
                            <td>${node.type}</td>
                        </tr>
                        <tr>
                            <td>状态:</td>
                            <td><span class="status-badge ${node.status}">${node.status}</span></td>
                        </tr>
                    </table>
                </div>

                <div class="detail-section">
                    <h4>性能指标</h4>
                    <div class="performance-charts">
                        <div class="chart">
                            <canvas id="cpuChart"></canvas>
                        </div>
                        <div class="chart">
                            <canvas id="memoryChart"></canvas>
                        </div>
                        <div class="chart">
                            <canvas id="networkChart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>运行日志</h4>
                    <div class="log-viewer">
                        <pre>${node.logs.join('\n')}</pre>
                    </div>
                </div>
            </div>
        `;
    }

    async restartNode(nodeId) {
        if (!confirm('确定要重启此节点吗？')) return;

        try {
            const response = await fetch(`/api/monitor/nodes/${nodeId}/restart`, {
                method: 'POST'
            });
            const result = await response.json();
            
            if (result.success) {
                showSuccess('节点重启指令已发送');
                this.loadNodes();
            } else {
                showError(result.message || '重启节点失败');
            }
        } catch (error) {
            console.error('Failed to restart node:', error);
            showError('重启节点失败');
        }
    }

    async troubleshootNode(nodeId) {
        try {
            const response = await fetch(`/api/monitor/nodes/${nodeId}/troubleshoot`);
            const data = await response.json();
            
            showModal({
                title: '节点诊断',
                content: this.renderTroubleshootInfo(data),
                width: '600px'
            });
        } catch (error) {
            console.error('Failed to troubleshoot node:', error);
            showError('节点诊断失败');
        }
    }

    renderTroubleshootInfo(data) {
        return `
            <div class="troubleshoot-info">
                <div class="diagnosis-section">
                    <h4>诊断结果</h4>
                    <ul class="diagnosis-list">
                        ${data.issues.map(issue => `
                            <li class="issue ${issue.severity}">
                                <span class="issue-title">${issue.title}</span>
                                <p class="issue-description">${issue.description}</p>
                                ${issue.solution ? `
                                    <div class="issue-solution">
                                        <strong>建议解决方案：</strong>
                                        <p>${issue.solution}</p>
                                    </div>
                                ` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>

                <div class="diagnosis-actions">
                    <button onclick="nodeMonitor.applyFix('${data.nodeId}')" 
                            class="btn-primary" 
                            ${data.canAutoFix ? '' : 'disabled'}>
                        自动修复
                    </button>
                    <button onclick="nodeMonitor.downloadDiagnosisReport('${data.nodeId}')" 
                            class="btn-secondary">
                        下载诊断报告
                    </button>
                </div>
            </div>
        `;
    }

    async applyFix(nodeId) {
        try {
            const response = await fetch(`/api/monitor/nodes/${nodeId}/fix`, {
                method: 'POST'
            });
            const result = await response.json();
            
            if (result.success) {
                showSuccess('修复指令已发送');
                this.loadNodes();
            } else {
                showError(result.message || '修复失败');
            }
        } catch (error) {
            console.error('Failed to apply fix:', error);
            showError('修复失败');
        }
    }

    async downloadDiagnosisReport(nodeId) {
        try {
            const response = await fetch(`/api/monitor/nodes/${nodeId}/report`);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `node-diagnosis-${nodeId}-${formatDate(new Date())}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Failed to download report:', error);
            showError('下载报告失败');
        }
    }
}

// 初始化节点监控
const nodeMonitor = new NodeMonitor();

// 辅助函数
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function showModal(options) {
    // 实现模态框显示逻辑
}

function showError(message) {
    // 实现错误提示逻辑
}

function showSuccess(message) {
    // 实现成功提示逻辑
} 