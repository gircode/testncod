class SyncManager {
    constructor() {
        this.syncs = [];
        this.filters = {
            source: 'all',
            target: 'all',
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
        this.loadSyncs();
        this.setupEventListeners();
        this.setupAutoRefresh();
    }

    async loadSyncs() {
        try {
            const response = await fetch('/api/data/syncs?' + this.buildQueryString());
            const data = await response.json();
            this.syncs = data.syncs;
            this.pagination.total = data.total;
            this.updateSyncTable();
            this.updatePagination();
            this.updateStats();
        } catch (error) {
            console.error('Failed to load syncs:', error);
            showError('加载同步列表失败');
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
        if (this.filters.target !== 'all') {
            params.append('target', this.filters.target);
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

    updateSyncTable() {
        const tbody = document.getElementById('syncTableBody');
        if (!tbody) return;

        tbody.innerHTML = this.syncs.map(sync => `
            <tr data-id="${sync.id}">
                <td><input type="checkbox" class="sync-select"></td>
                <td>${sync.id}</td>
                <td>${sync.source_node}</td>
                <td>${sync.target_node}</td>
                <td>${sync.data_type}</td>
                <td><span class="status-badge ${sync.status}">${sync.status}</span></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${sync.progress}%">
                            ${sync.progress}%
                        </div>
                    </div>
                </td>
                <td>${formatTime(sync.start_time)}</td>
                <td>
                    <div class="actions">
                        <button onclick="syncManager.viewSyncDetails('${sync.id}')" class="btn-info btn-small">详情</button>
                        ${sync.status === 'pending' || sync.status === 'running' ? `
                            <button onclick="syncManager.pauseSync('${sync.id}')" class="btn-warning btn-small">暂停</button>
                            <button onclick="syncManager.cancelSync('${sync.id}')" class="btn-danger btn-small">取消</button>
                        ` : ''}
                        ${sync.status === 'paused' ? `
                            <button onclick="syncManager.resumeSync('${sync.id}')" class="btn-primary btn-small">恢复</button>
                        ` : ''}
                        ${sync.status === 'failed' ? `
                            <button onclick="syncManager.retrySync('${sync.id}')" class="btn-warning btn-small">重试</button>
                        ` : ''}
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
                <button onclick="syncManager.goToPage(1)" ${this.pagination.page === 1 ? 'disabled' : ''}>首页</button>
                <button onclick="syncManager.goToPage(${this.pagination.page - 1})" ${this.pagination.page === 1 ? 'disabled' : ''}>上一页</button>
                <span>第 ${this.pagination.page} 页 / 共 ${totalPages} 页</span>
                <button onclick="syncManager.goToPage(${this.pagination.page + 1})" ${this.pagination.page === totalPages ? 'disabled' : ''}>下一页</button>
                <button onclick="syncManager.goToPage(${totalPages})" ${this.pagination.page === totalPages ? 'disabled' : ''}>末页</button>
            `;
        }
        pagination.innerHTML = html;
    }

    async updateStats() {
        try {
            const response = await fetch('/api/data/syncs/stats');
            const stats = await response.json();
            
            // 更新状态统计
            Object.entries(stats).forEach(([key, value]) => {
                const element = document.querySelector(`.status-item .value.${key}`);
                if (element) {
                    element.textContent = value;
                }
            });

            // 更新性能统计
            document.querySelector('.performance-stats .avg-speed').textContent = stats.avg_speed;
            document.querySelector('.performance-stats .total-data').textContent = formatDataSize(stats.total_data);
            document.querySelector('.performance-stats .success-rate').textContent = `${stats.success_rate}%`;
        } catch (error) {
            console.error('Failed to load sync stats:', error);
        }
    }

    setupEventListeners() {
        // 源节点筛选
        document.getElementById('sourceFilter')?.addEventListener('change', e => {
            this.filters.source = e.target.value;
            this.loadSyncs();
        });

        // 目标节点筛选
        document.getElementById('targetFilter')?.addEventListener('change', e => {
            this.filters.target = e.target.value;
            this.loadSyncs();
        });

        // 状态筛选
        document.getElementById('statusFilter')?.addEventListener('change', e => {
            this.filters.status = e.target.value;
            this.loadSyncs();
        });

        // 日期范围筛选
        document.getElementById('startDate')?.addEventListener('change', e => {
            this.filters.dateRange.start = e.target.value;
            this.loadSyncs();
        });

        document.getElementById('endDate')?.addEventListener('change', e => {
            this.filters.dateRange.end = e.target.value;
            this.loadSyncs();
        });

        // 同步表单提交
        document.getElementById('syncForm')?.addEventListener('submit', e => this.saveSync(e));

        // 数据类型切换
        document.getElementById('dataType')?.addEventListener('change', e => {
            const customConfig = document.getElementById('customDataConfig');
            if (customConfig) {
                customConfig.style.display = e.target.value === 'custom' ? 'block' : 'none';
            }
        });

        // 执行计划切换
        document.getElementById('schedule')?.addEventListener('change', e => {
            this.toggleScheduleConfig(e.target.value);
        });
    }

    setupAutoRefresh() {
        // 每30秒自动刷新一次
        setInterval(() => this.loadSyncs(), 30000);
    }

    toggleScheduleConfig(type) {
        const config = document.getElementById('scheduleConfig');
        if (!config) return;

        switch (type) {
            case 'immediate':
                config.style.display = 'none';
                break;
            case 'scheduled':
                config.style.display = 'block';
                config.innerHTML = `
                    <div class="form-group">
                        <label for="scheduleTime">执行时间</label>
                        <input type="datetime-local" id="scheduleTime" name="schedule_time" required>
                    </div>
                `;
                break;
            case 'recurring':
                config.style.display = 'block';
                config.innerHTML = `
                    <div class="form-group">
                        <label for="recurringType">重复类型</label>
                        <select id="recurringType" name="recurring_type" required>
                            <option value="daily">每天</option>
                            <option value="weekly">每周</option>
                            <option value="monthly">每月</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="recurringTime">执行时间</label>
                        <input type="time" id="recurringTime" name="recurring_time" required>
                    </div>
                `;
                break;
        }
    }

    // ... 其他方法的实现（创建、暂停、恢复、取消等）
}

// 初始化同步管理器
const syncManager = new SyncManager();

// 辅助函数
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function formatDataSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

function showError(message) {
    // 实现错误提示逻辑
}

function showSuccess(message) {
    // 实现成功提示逻辑
} 