class UserManager {
    constructor() {
        this.users = [];
        this.filters = {
            role: 'all',
            status: 'all',
            department: 'all',
            search: ''
        };
        this.pagination = {
            page: 1,
            pageSize: 10,
            total: 0
        };
        this.init();
    }

    init() {
        this.loadUsers();
        this.setupEventListeners();
        this.initRoleDistributionChart();
    }

    async loadUsers() {
        try {
            const response = await fetch('/api/users?' + this.buildQueryString());
            const data = await response.json();
            this.users = data.users;
            this.pagination.total = data.total;
            this.updateUsersTable();
            this.updatePagination();
            this.updateStats();
        } catch (error) {
            console.error('Failed to load users:', error);
            showError('加载用户列表失败');
        }
    }

    buildQueryString() {
        const params = new URLSearchParams({
            page: this.pagination.page,
            pageSize: this.pagination.pageSize
        });

        if (this.filters.role !== 'all') {
            params.append('role', this.filters.role);
        }
        if (this.filters.status !== 'all') {
            params.append('status', this.filters.status);
        }
        if (this.filters.department !== 'all') {
            params.append('department', this.filters.department);
        }
        if (this.filters.search) {
            params.append('search', this.filters.search);
        }

        return params.toString();
    }

    updateUsersTable() {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;

        tbody.innerHTML = this.users.map(user => `
            <tr data-id="${user.id}">
                <td><input type="checkbox" class="user-select"></td>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.realname}</td>
                <td>${user.roles.map(role => `<span class="role-badge">${role}</span>`).join('')}</td>
                <td>${user.department}</td>
                <td><span class="status-badge ${user.status}">${user.status}</span></td>
                <td>${user.last_login ? formatTime(user.last_login) : '-'}</td>
                <td>${formatTime(user.created_at)}</td>
                <td>
                    <div class="actions">
                        <button onclick="userManager.editUser('${user.id}')" class="btn-info btn-small">编辑</button>
                        <button onclick="userManager.resetPassword('${user.id}')" class="btn-warning btn-small">重置密码</button>
                        ${user.status === 'locked' ? `
                            <button onclick="userManager.unlockUser('${user.id}')" class="btn-success btn-small">解锁</button>
                        ` : `
                            <button onclick="userManager.lockUser('${user.id}')" class="btn-warning btn-small">锁定</button>
                        `}
                        <button onclick="userManager.deleteUser('${user.id}')" class="btn-danger btn-small">删除</button>
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
                <button onclick="userManager.goToPage(1)" ${this.pagination.page === 1 ? 'disabled' : ''}>首页</button>
                <button onclick="userManager.goToPage(${this.pagination.page - 1})" ${this.pagination.page === 1 ? 'disabled' : ''}>上一页</button>
                <span>第 ${this.pagination.page} 页 / 共 ${totalPages} 页</span>
                <button onclick="userManager.goToPage(${this.pagination.page + 1})" ${this.pagination.page === totalPages ? 'disabled' : ''}>下一页</button>
                <button onclick="userManager.goToPage(${totalPages})" ${this.pagination.page === totalPages ? 'disabled' : ''}>末页</button>
            `;
        }
        pagination.innerHTML = html;
    }

    async updateStats() {
        try {
            const response = await fetch('/api/users/stats');
            const stats = await response.json();
            
            // 更新统计信息
            document.querySelector('.stats-grid .total-users').textContent = stats.total_users;
            document.querySelector('.stats-grid .active-users').textContent = stats.active_users;
            document.querySelector('.stats-grid .online-users').textContent = stats.online_users;
            document.querySelector('.stats-grid .locked-users').textContent = stats.locked_users;

            // 更新角色分布图表
            this.updateRoleDistributionChart(stats.role_distribution);
        } catch (error) {
            console.error('Failed to load user stats:', error);
        }
    }

    initRoleDistributionChart() {
        const ctx = document.getElementById('roleDistributionChart');
        if (!ctx) return;

        this.roleChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#4CAF50',
                        '#2196F3',
                        '#FF9800',
                        '#9C27B0',
                        '#F44336'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }

    updateRoleDistributionChart(distribution) {
        if (!this.roleChart) return;

        this.roleChart.data.labels = Object.keys(distribution);
        this.roleChart.data.datasets[0].data = Object.values(distribution);
        this.roleChart.update();
    }

    setupEventListeners() {
        // 角色筛选
        document.getElementById('roleFilter')?.addEventListener('change', e => {
            this.filters.role = e.target.value;
            this.loadUsers();
        });

        // 状态筛选
        document.getElementById('statusFilter')?.addEventListener('change', e => {
            this.filters.status = e.target.value;
            this.loadUsers();
        });

        // 部门筛选
        document.getElementById('departmentFilter')?.addEventListener('change', e => {
            this.filters.department = e.target.value;
            this.loadUsers();
        });

        // 用户表单提交
        document.getElementById('userForm')?.addEventListener('submit', e => this.saveUser(e));
    }

    async saveUser(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        
        // 处理多选的角色
        data.roles = formData.getAll('roles[]');

        const userId = e.target.dataset.id;
        try {
            const response = await fetch(`/api/users${userId ? `/${userId}` : ''}`, {
                method: userId ? 'PUT' : 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                showSuccess(userId ? '用户更新成功' : '用户创建成功');
                this.closeUserDialog();
                this.loadUsers();
            } else {
                const error = await response.json();
                showError(error.message || '保存失败');
            }
        } catch (error) {
            console.error('Failed to save user:', error);
            showError('保存失败');
        }
    }

    // ... 其他方法的实现（创建、编辑、删除、重置密码等）
}

// 初始化用户管理器
const userManager = new UserManager();

// 辅助函数
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function showError(message) {
    // 实现错误提示逻辑
}

function showSuccess(message) {
    // 实现成功提示逻辑
} 