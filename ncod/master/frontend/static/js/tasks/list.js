class TaskManager {
    constructor() {
        this.tasks = [];
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
        this.loadTasks();
        this.setupEventListeners();
    }

    async loadTasks() {
        try {
            const response = await fetch('/api/tasks?' + this.buildQueryString());
            const data = await response.json();
            this.tasks = data.tasks;
            this.pagination.total = data.total;
            this.updateTasksTable();
            this.updatePagination();
        } catch (error) {
            console.error('Failed to load tasks:', error);
            showError('加载任务列表失败');
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

    updateTasksTable() {
        const tbody = document.getElementById('tasksTableBody');
        if (!tbody) return;

        tbody.innerHTML = this.tasks.map(task => `
            <tr data-id="${task.id}">
                <td><input type="checkbox" class="task-select"></td>
                <td>${task.id}</td>
                <td>${task.name}</td>
                <td><span class="task-type ${task.type}">${task.type}</span></td>
                <td><span class="status-badge ${task.status}">${task.status}</span></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${task.progress}%">
                            ${task.progress}%
                        </div>
                    </div>
                </td>
                <td>${formatTime(task.created_at)}</td>
                <td>
                    <div class="actions">
                        <button onclick="taskManager.viewTaskDetails('${task.id}')" class="btn-info btn-small">详情</button>
                        ${task.status === 'pending' || task.status === 'running' ? `
                            <button onclick="taskManager.cancelTask('${task.id}')" class="btn-danger btn-small">取消</button>
                        ` : ''}
                        ${task.status === 'failed' ? `
                            <button onclick="taskManager.retryTask('${task.id}')" class="btn-warning btn-small">重试</button>
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
                <button onclick="taskManager.goToPage(1)" ${this.pagination.page === 1 ? 'disabled' : ''}>首页</button>
                <button onclick="taskManager.goToPage(${this.pagination.page - 1})" ${this.pagination.page === 1 ? 'disabled' : ''}>上一页</button>
                <span>第 ${this.pagination.page} 页 / 共 ${totalPages} 页</span>
                <button onclick="taskManager.goToPage(${this.pagination.page + 1})" ${this.pagination.page === totalPages ? 'disabled' : ''}>下一页</button>
                <button onclick="taskManager.goToPage(${totalPages})" ${this.pagination.page === totalPages ? 'disabled' : ''}>末页</button>
            `;
        }
        pagination.innerHTML = html;
    }

    goToPage(page) {
        this.pagination.page = page;
        this.loadTasks();
    }

    filterByType(type) {
        this.filters.type = type;
        this.pagination.page = 1;
        this.loadTasks();
    }

    filterByStatus(status) {
        this.filters.status = status;
        this.pagination.page = 1;
        this.loadTasks();
    }

    filterByDate(date, type) {
        this.filters.dateRange[type] = date;
        this.pagination.page = 1;
        this.loadTasks();
    }

    searchTasks(keyword) {
        clearTimeout(this._searchTimer);
        this._searchTimer = setTimeout(() => {
            // 实现搜索逻辑
        }, 300);
    }

    async createTask() {
        document.getElementById('taskForm').reset();
        document.getElementById('taskDialog').style.display = 'block';
    }

    async saveTask(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.closeTaskDialog();
                this.loadTasks();
                showSuccess('任务创建成功');
            } else {
                const error = await response.json();
                showError(error.message || '任务创建失败');
            }
        } catch (error) {
            console.error('Failed to create task:', error);
            showError('任务创建失败');
        }
    }

    closeTaskDialog() {
        document.getElementById('taskDialog').style.display = 'none';
    }

    async viewTaskDetails(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`);
            const task = await response.json();
            
            showModal({
                title: '任务详情',
                content: this.renderTaskDetails(task),
                width: '800px'
            });
        } catch (error) {
            console.error('Failed to load task details:', error);
            showError('加载任务详情失败');
        }
    }

    renderTaskDetails(task) {
        return `
            <div class="task-details">
                <div class="detail-section">
                    <h4>基本信息</h4>
                    <table class="detail-table">
                        <tr>
                            <td>任务ID:</td>
                            <td>${task.id}</td>
                        </tr>
                        <tr>
                            <td>任务名称:</td>
                            <td>${task.name}</td>
                        </tr>
                        <tr>
                            <td>任务类型:</td>
                            <td>${task.type}</td>
                        </tr>
                        <tr>
                            <td>创建时间:</td>
                            <td>${formatTime(task.created_at)}</td>
                        </tr>
                        <tr>
                            <td>状态:</td>
                            <td><span class="status-badge ${task.status}">${task.status}</span></td>
                        </tr>
                        <tr>
                            <td>进度:</td>
                            <td>${task.progress}%</td>
                        </tr>
                    </table>
                </div>

                <div class="detail-section">
                    <h4>执行记录</h4>
                    <div class="execution-timeline">
                        ${task.timeline.map(event => `
                            <div class="timeline-event">
                                <span class="time">${formatTime(event.time)}</span>
                                <span class="event">${event.message}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                ${task.error ? `
                    <div class="detail-section error-section">
                        <h4>错误信息</h4>
                        <div class="error-details">
                            <pre>${task.error}</pre>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    async cancelTask(taskId) {
        if (!confirm('确定要取消此任务吗？')) return;

        try {
            const response = await fetch(`/api/tasks/${taskId}/cancel`, {
                method: 'POST'
            });
            
            if (response.ok) {
                showSuccess('任务已取消');
                this.loadTasks();
            } else {
                const error = await response.json();
                showError(error.message || '取消任务失败');
            }
        } catch (error) {
            console.error('Failed to cancel task:', error);
            showError('取消任务失败');
        }
    }

    async retryTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/retry`, {
                method: 'POST'
            });
            
            if (response.ok) {
                showSuccess('任务已重新提交');
                this.loadTasks();
            } else {
                const error = await response.json();
                showError(error.message || '重试任务失败');
            }
        } catch (error) {
            console.error('Failed to retry task:', error);
            showError('重试任务失败');
        }
    }

    setupEventListeners() {
        const taskForm = document.getElementById('taskForm');
        if (taskForm) {
            taskForm.addEventListener('submit', e => this.saveTask(e));
        }
    }

    toggleScheduleOptions(type) {
        const options = document.getElementById('scheduleOptions');
        if (!options) return;

        switch (type) {
            case 'immediate':
                options.style.display = 'none';
                break;
            case 'once':
                options.style.display = 'block';
                options.innerHTML = `
                    <div class="form-group">
                        <label>执行时间</label>
                        <input type="datetime-local" name="schedule_time" required>
                    </div>
                `;
                break;
            case 'recurring':
                options.style.display = 'block';
                options.innerHTML = `
                    <div class="form-group">
                        <label>重复类型</label>
                        <select name="recurring_type" required>
                            <option value="daily">每天</option>
                            <option value="weekly">每周</option>
                            <option value="monthly">每月</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>执行时间</label>
                        <input type="time" name="recurring_time" required>
                    </div>
                `;
                break;
        }
    }

    showBatchActions() {
        const selectedTasks = Array.from(document.querySelectorAll('.task-select:checked'))
            .map(checkbox => checkbox.closest('tr').dataset.id);

        if (selectedTasks.length === 0) {
            showError('请先选择要操作的任务');
            return;
        }

        showModal({
            title: '批量操作',
            content: `
                <div class="batch-actions">
                    <button onclick="taskManager.batchCancel(${JSON.stringify(selectedTasks)})" class="btn-danger">
                        取消所选任务
                    </button>
                    <button onclick="taskManager.batchRetry(${JSON.stringify(selectedTasks)})" class="btn-warning">
                        重试失败任务
                    </button>
                    <button onclick="taskManager.batchDelete(${JSON.stringify(selectedTasks)})" class="btn-danger">
                        删除所选任务
                    </button>
                </div>
            `,
            width: '400px'
        });
    }

    async batchCancel(taskIds) {
        try {
            const response = await fetch('/api/tasks/batch/cancel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ taskIds })
            });
            
            if (response.ok) {
                showSuccess('批量取消任务成功');
                this.loadTasks();
            } else {
                const error = await response.json();
                showError(error.message || '批量取消任务失败');
            }
        } catch (error) {
            console.error('Failed to batch cancel tasks:', error);
            showError('批量取消任务失败');
        }
    }

    async batchRetry(taskIds) {
        try {
            const response = await fetch('/api/tasks/batch/retry', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ taskIds })
            });
            
            if (response.ok) {
                showSuccess('批量重试任务成功');
                this.loadTasks();
            } else {
                const error = await response.json();
                showError(error.message || '批量重试任务失败');
            }
        } catch (error) {
            console.error('Failed to batch retry tasks:', error);
            showError('批量重试任务失败');
        }
    }

    async batchDelete(taskIds) {
        if (!confirm('确定要删除所选任务吗？此操作不可恢复。')) return;

        try {
            const response = await fetch('/api/tasks/batch/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ taskIds })
            });
            
            if (response.ok) {
                showSuccess('批量删除任务成功');
                this.loadTasks();
            } else {
                const error = await response.json();
                showError(error.message || '批量删除任务失败');
            }
        } catch (error) {
            console.error('Failed to batch delete tasks:', error);
            showError('批量删除任务失败');
        }
    }

    toggleSelectAll(checkbox) {
        const taskCheckboxes = document.querySelectorAll('.task-select');
        taskCheckboxes.forEach(cb => cb.checked = checkbox.checked);
    }
}

// 初始化任务管理器
const taskManager = new TaskManager();

// 辅助函数
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleString();
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