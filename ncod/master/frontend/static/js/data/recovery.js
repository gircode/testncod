class RecoveryManager {
    constructor() {
        this.recoveries = [];
        this.filters = {
            source: 'all',
            status: 'all',
            dateRange: {
                start: null,
                end: null
            }
        };
        this.pagination = {
            page: 1,
            pageSize: 10,
            total: 0
        };
        this.init();
    }

    init() {
        this.loadRecoveries();
        this.setupEventListeners();
        this.setupAutoRefresh();
    }

    async loadRecoveries() {
        try {
            const response = await fetch('/api/data/recoveries?' + this.buildQueryString());
            const data = await response.json();
            this.recoveries = data.recoveries;
            this.pagination.total = data.total;
            this.updateRecoveryTable();
            this.updatePagination();
            this.updateStats();
        } catch (error) {
            console.error('Failed to load recoveries:', error);
            showError('加载恢复列表失败');
        }
    }

    buildQueryString() {
        const params = new URLSearchParams({
            page: this.pagination.page,
            pageSize: this.pagination.pageSize
        });

        if (this.filters.source !== 'all') {
            params.append('source', this.filters.source);
        }
        if (this.filters.status !== 'all') {
            params.append('status', this.filters.status);
        }
        if (this.filters.dateRange.start) {
            params.append('startDate', this.filters.dateRange.start);
        }
        if (this.filters.dateRange.end) {
            params.append('endDate', this.filters.dateRange.end);
        }

        return params.toString();
    }

    updateRecoveryTable() {
        const tbody = document.getElementById('recoveryTableBody');
        if (!tbody) return;

        tbody.innerHTML = this.recoveries.map(recovery => `
            <tr data-id="${recovery.id}">
                <td><input type="checkbox" class="recovery-select"></td>
                <td>${recovery.id}</td>
                <td>${recovery.name}</td>
                <td>${recovery.backup_name}</td>
                <td>${recovery.target_location}</td>
                <td><span class="status-badge ${recovery.status}">${recovery.status}</span></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${recovery.progress}%">
                            ${recovery.progress}%
                        </div>
                    </div>
                </td>
                <td>${formatTime(recovery.start_time)}</td>
                <td>${recovery.completed_at ? formatTime(recovery.completed_at) : '-'}</td>
                <td>
                    <div class="actions">
                        <button onclick="recoveryManager.viewRecoveryDetails('${recovery.id}')" class="btn-info btn-small">详情</button>
                        ${recovery.status === 'running' ? `
                            <button onclick="recoveryManager.pauseRecovery('${recovery.id}')" class="btn-warning btn-small">暂停</button>
                            <button onclick="recoveryManager.cancelRecovery('${recovery.id}')" class="btn-danger btn-small">取消</button>
                        ` : ''}
                        ${recovery.status === 'paused' ? `
                            <button onclick="recoveryManager.resumeRecovery('${recovery.id}')" class="btn-primary btn-small">恢复</button>
                        ` : ''}
                        ${recovery.status === 'failed' ? `
                            <button onclick="recoveryManager.retryRecovery('${recovery.id}')" class="btn-warning btn-small">重试</button>
                        ` : ''}
                        <button onclick="recoveryManager.deleteRecovery('${recovery.id}')" class="btn-danger btn-small">删除</button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    updatePagination() {
        const totalPages = Math.ceil(this.pagination.total / this.pagination.pageSize);
        const pagination = document.querySelector('.pagination');
        if (!pagination) return;

        let html = '';
        if (totalPages > 1) {
            html = `
                <button onclick="recoveryManager.goToPage(1)" ${this.pagination.page === 1 ? 'disabled' : ''}>首页</button>
                <button onclick="recoveryManager.goToPage(${this.pagination.page - 1})" ${this.pagination.page === 1 ? 'disabled' : ''}>上一页</button>
                <span>第 ${this.pagination.page} 页 / 共 ${totalPages} 页</span>
                <button onclick="recoveryManager.goToPage(${this.pagination.page + 1})" ${this.pagination.page === totalPages ? 'disabled' : ''}>下一页</button>
                <button onclick="recoveryManager.goToPage(${totalPages})" ${this.pagination.page === totalPages ? 'disabled' : ''}>末页</button>
            `;
        }
        pagination.innerHTML = html;
    }

    async updateStats() {
        try {
            const response = await fetch('/api/data/recoveries/stats');
            const stats = await response.json();
            
            // 更新统计信息
            document.querySelector('.stats-grid .total-recoveries').textContent = stats.total_recoveries;
            document.querySelector('.stats-grid .success-rate').textContent = `${stats.success_rate}%`;
            document.querySelector('.stats-grid .avg-duration').textContent = formatDuration(stats.avg_duration);
            document.querySelector('.stats-grid .last-recovery').textContent = formatTime(stats.last_recovery);
        } catch (error) {
            console.error('Failed to load recovery stats:', error);
        }
    }

    setupEventListeners() {
        // 源备份筛选
        document.getElementById('sourceFilter')?.addEventListener('change', e => {
            this.filters.source = e.target.value;
            this.loadRecoveries();
        });

        // 状态筛选
        document.getElementById('statusFilter')?.addEventListener('change', e => {
            this.filters.status = e.target.value;
            this.loadRecoveries();
        });

        // 日期范围筛选
        document.getElementById('startDate')?.addEventListener('change', e => {
            this.filters.dateRange.start = e.target.value;
            this.loadRecoveries();
        });

        document.getElementById('endDate')?.addEventListener('change', e => {
            this.filters.dateRange.end = e.target.value;
            this.loadRecoveries();
        });

        // 恢复表单提交
        document.getElementById('recoveryForm')?.addEventListener('submit', e => this.saveRecovery(e));

        // 目标位置切换
        document.getElementById('targetLocation')?.addEventListener('change', e => {
            const customConfig = document.getElementById('customLocationConfig');
            if (customConfig) {
                customConfig.style.display = e.target.value === 'custom' ? 'block' : 'none';
            }
        });

        // 源备份切换时更新恢复点
        document.getElementById('backupSource')?.addEventListener('change', e => {
            this.loadRecoveryPoints(e.target.value);
        });
    }

    async loadRecoveryPoints(backupId) {
        try {
            const response = await fetch(`/api/data/backups/${backupId}/points`);
            const points = await response.json();
            
            const select = document.getElementById('recoveryPoint');
            if (select) {
                select.innerHTML = points.map(point => `
                    <option value="${point.id}">${formatTime(point.time)} - ${point.type}</option>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load recovery points:', error);
            showError('加载恢复点失败');
        }
    }

    setupAutoRefresh() {
        // 每30秒自动刷新一次
        setInterval(() => this.loadRecoveries(), 30000);
    }

    // ... 其他方法的实现（创建、暂停、恢复、取消等）
}

// 初始化恢复管理器
const recoveryManager = new RecoveryManager();

// 辅助函数
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    const parts = [];
    if (hours > 0) parts.push(`${hours}小时`);
    if (minutes > 0) parts.push(`${minutes}分钟`);
    if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds}秒`);
    
    return parts.join(' ');
}

function showError(message) {
    // 实现错误提示逻辑
}

function showSuccess(message) {
    // 实现成功提示逻辑
} 