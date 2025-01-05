class BackupManager {
    constructor() {
        this.backups = [];
        this.filters = {
            type: 'all',
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
        this.loadBackups();
        this.setupEventListeners();
        this.setupAutoRefresh();
    }

    async loadBackups() {
        try {
            const response = await fetch('/api/data/backups?' + this.buildQueryString());
            const data = await response.json();
            this.backups = data.backups;
            this.pagination.total = data.total;
            this.updateBackupTable();
            this.updatePagination();
            this.updateStats();
        } catch (error) {
            console.error('Failed to load backups:', error);
            showError('加载备份列表失败');
        }
    }

    buildQueryString() {
        const params = new URLSearchParams({
            page: this.pagination.page,
            pageSize: this.pagination.pageSize
        });

        if (this.filters.type !== 'all') {
            params.append('type', this.filters.type);
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

    updateBackupTable() {
        const tbody = document.getElementById('backupTableBody');
        if (!tbody) return;

        tbody.innerHTML = this.backups.map(backup => `
            <tr data-id="${backup.id}">
                <td><input type="checkbox" class="backup-select"></td>
                <td>${backup.id}</td>
                <td>${backup.name}</td>
                <td><span class="type-badge ${backup.type}">${backup.type}</span></td>
                <td>${formatSize(backup.size)}</td>
                <td><span class="status-badge ${backup.status}">${backup.status}</span></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${backup.progress}%">
                            ${backup.progress}%
                        </div>
                    </div>
                </td>
                <td>${formatTime(backup.start_time)}</td>
                <td>${backup.completed_at ? formatTime(backup.completed_at) : '-'}</td>
                <td>
                    <div class="actions">
                        <button onclick="backupManager.viewBackupDetails('${backup.id}')" class="btn-info btn-small">详情</button>
                        ${backup.status === 'completed' ? `
                            <button onclick="backupManager.downloadBackup('${backup.id}')" class="btn-primary btn-small">下载</button>
                            <button onclick="backupManager.restoreBackup('${backup.id}')" class="btn-warning btn-small">恢复</button>
                        ` : ''}
                        ${backup.status === 'running' ? `
                            <button onclick="backupManager.cancelBackup('${backup.id}')" class="btn-danger btn-small">取消</button>
                        ` : ''}
                        ${backup.status === 'failed' ? `
                            <button onclick="backupManager.retryBackup('${backup.id}')" class="btn-warning btn-small">重试</button>
                        ` : ''}
                        <button onclick="backupManager.deleteBackup('${backup.id}')" class="btn-danger btn-small">删除</button>
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
                <button onclick="backupManager.goToPage(1)" ${this.pagination.page === 1 ? 'disabled' : ''}>首页</button>
                <button onclick="backupManager.goToPage(${this.pagination.page - 1})" ${this.pagination.page === 1 ? 'disabled' : ''}>上一页</button>
                <span>第 ${this.pagination.page} 页 / 共 ${totalPages} 页</span>
                <button onclick="backupManager.goToPage(${this.pagination.page + 1})" ${this.pagination.page === totalPages ? 'disabled' : ''}>下一页</button>
                <button onclick="backupManager.goToPage(${totalPages})" ${this.pagination.page === totalPages ? 'disabled' : ''}>末页</button>
            `;
        }
        pagination.innerHTML = html;
    }

    async updateStats() {
        try {
            const response = await fetch('/api/data/backups/stats');
            const stats = await response.json();
            
            // 更新统计信息
            document.querySelector('.stats-grid .total-backups').textContent = stats.total_backups;
            document.querySelector('.stats-grid .total-size').textContent = formatSize(stats.total_size);
            document.querySelector('.stats-grid .last-backup').textContent = formatTime(stats.last_backup);
            document.querySelector('.stats-grid .success-rate').textContent = `${stats.success_rate}%`;

            // 更新存储使用情况
            const progressRing = document.querySelector('.progress-ring path:last-child');
            progressRing.style.strokeDasharray = `${stats.storage_usage}, 100`;
            document.querySelector('.progress-text').textContent = `${stats.storage_usage}%`;
            
            document.querySelector('.storage-details .used-space').textContent = formatSize(stats.used_space);
            document.querySelector('.storage-details .free-space').textContent = formatSize(stats.free_space);
            document.querySelector('.storage-details .total-space').textContent = formatSize(stats.total_space);
        } catch (error) {
            console.error('Failed to load backup stats:', error);
        }
    }

    setupEventListeners() {
        // 备份类型筛选
        document.getElementById('typeFilter')?.addEventListener('change', e => {
            this.filters.type = e.target.value;
            this.loadBackups();
        });

        // 状态筛选
        document.getElementById('statusFilter')?.addEventListener('change', e => {
            this.filters.status = e.target.value;
            this.loadBackups();
        });

        // 日期范围筛选
        document.getElementById('startDate')?.addEventListener('change', e => {
            this.filters.dateRange.start = e.target.value;
            this.loadBackups();
        });

        document.getElementById('endDate')?.addEventListener('change', e => {
            this.filters.dateRange.end = e.target.value;
            this.loadBackups();
        });

        // 备份表单提交
        document.getElementById('backupForm')?.addEventListener('submit', e => this.saveBackup(e));

        // 加密方式切换
        document.getElementById('encryption')?.addEventListener('change', e => {
            const keyGroup = document.getElementById('encryptionKey');
            if (keyGroup) {
                keyGroup.style.display = e.target.value === 'none' ? 'none' : 'block';
            }
        });

        // 执行计划切换
        document.getElementById('schedule')?.addEventListener('change', e => {
            this.toggleScheduleConfig(e.target.value);
        });
    }

    setupAutoRefresh() {
        // 每30秒自动刷新一次
        setInterval(() => this.loadBackups(), 30000);
    }

    // ... 其他方法的实现（创建、下载、恢复、删除等）
}

// 初始化备份管理器
const backupManager = new BackupManager();

// 辅助函数
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function formatSize(bytes) {
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