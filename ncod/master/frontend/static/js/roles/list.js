class RoleManager {
    constructor() {
        this.roles = [];
        this.filters = {
            type: 'all',
            status: 'all'
        };
        this.pagination = {
            page: 1,
            pageSize: 10,
            total: 0
        };
        this.init();
    }

    init() {
        this.loadRoles();
        this.setupEventListeners();
        this.initPermissionDistributionChart();
        this.setupPermissionTree();
    }

    async loadRoles() {
        try {
            const response = await fetch('/api/roles?' + this.buildQueryString());
            const data = await response.json();
            this.roles = data.roles;
            this.pagination.total = data.total;
            this.updateRolesTable();
            this.updatePagination();
            this.updateStats();
        } catch (error) {
            console.error('Failed to load roles:', error);
            showError('加载角色列表失败');
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

        return params.toString();
    }

    updateRolesTable() {
        const tbody = document.getElementById('rolesTableBody');
        if (!tbody) return;

        tbody.innerHTML = this.roles.map(role => `
            <tr data-id="${role.id}">
                <td><input type="checkbox" class="role-select"></td>
                <td>${role.id}</td>
                <td>${role.name}</td>
                <td><span class="type-badge ${role.type}">${role.type}</span></td>
                <td>${role.description || '-'}</td>
                <td>${role.user_count}</td>
                <td><span class="status-badge ${role.status}">${role.status}</span></td>
                <td>${formatTime(role.created_at)}</td>
                <td>
                    <div class="actions">
                        <button onclick="roleManager.editRole('${role.id}')" class="btn-info btn-small">编辑</button>
                        <button onclick="roleManager.viewUsers('${role.id}')" class="btn-primary btn-small">查看用户</button>
                        ${role.type === 'custom' ? `
                            <button onclick="roleManager.deleteRole('${role.id}')" class="btn-danger btn-small">删除</button>
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
                <button onclick="roleManager.goToPage(1)" ${this.pagination.page === 1 ? 'disabled' : ''}>首页</button>
                <button onclick="roleManager.goToPage(${this.pagination.page - 1})" ${this.pagination.page === 1 ? 'disabled' : ''}>上一页</button>
                <span>第 ${this.pagination.page} 页 / 共 ${totalPages} 页</span>
                <button onclick="roleManager.goToPage(${this.pagination.page + 1})" ${this.pagination.page === totalPages ? 'disabled' : ''}>下一页</button>
                <button onclick="roleManager.goToPage(${totalPages})" ${this.pagination.page === totalPages ? 'disabled' : ''}>末页</button>
            `;
        }
        pagination.innerHTML = html;
    }

    async updateStats() {
        try {
            const response = await fetch('/api/roles/stats');
            const stats = await response.json();
            
            // 更新统计信息
            document.querySelector('.stats-grid .total-roles').textContent = stats.total_roles;
            document.querySelector('.stats-grid .system-roles').textContent = stats.system_roles;
            document.querySelector('.stats-grid .custom-roles').textContent = stats.custom_roles;
            document.querySelector('.stats-grid .unassigned-users').textContent = stats.unassigned_users;

            // 更新权限分布图表
            this.updatePermissionDistributionChart(stats.permission_distribution);
        } catch (error) {
            console.error('Failed to load role stats:', error);
        }
    }

    initPermissionDistributionChart() {
        const ctx = document.getElementById('permissionDistributionChart');
        if (!ctx) return;

        this.permissionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '权限数量',
                    data: [],
                    backgroundColor: '#2196F3'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updatePermissionDistributionChart(distribution) {
        if (!this.permissionChart) return;

        this.permissionChart.data.labels = Object.keys(distribution);
        this.permissionChart.data.datasets[0].data = Object.values(distribution);
        this.permissionChart.update();
    }

    setupPermissionTree() {
        // 处理模块级别的复选框
        document.querySelectorAll('.module-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', e => {
                const moduleItem = e.target.closest('.module-item');
                const permissions = moduleItem.querySelectorAll('.permission-checkbox');
                permissions.forEach(perm => perm.checked = e.target.checked);
            });
        });

        // 处理权限级别的复选框
        document.querySelectorAll('.permission-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', e => {
                const moduleItem = e.target.closest('.module-item');
                const moduleCheckbox = moduleItem.querySelector('.module-checkbox');
                const permissions = moduleItem.querySelectorAll('.permission-checkbox');
                const allChecked = Array.from(permissions).every(perm => perm.checked);
                const someChecked = Array.from(permissions).some(perm => perm.checked);
                
                moduleCheckbox.checked = allChecked;
                moduleCheckbox.indeterminate = !allChecked && someChecked;
            });
        });
    }

    setupEventListeners() {
        // 角色类型筛选
        document.getElementById('typeFilter')?.addEventListener('change', e => {
            this.filters.type = e.target.value;
            this.loadRoles();
        });

        // 状态筛选
        document.getElementById('statusFilter')?.addEventListener('change', e => {
            this.filters.status = e.target.value;
            this.loadRoles();
        });

        // 角色表单提交
        document.getElementById('roleForm')?.addEventListener('submit', e => this.saveRole(e));
    }

    async saveRole(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        
        // 处理权限列表
        data.permissions = formData.getAll('permissions[]');

        const roleId = e.target.dataset.id;
        try {
            const response = await fetch(`/api/roles${roleId ? `/${roleId}` : ''}`, {
                method: roleId ? 'PUT' : 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                showSuccess(roleId ? '角色更新成功' : '角色创建成功');
                this.closeRoleDialog();
                this.loadRoles();
            } else {
                const error = await response.json();
                showError(error.message || '保存失败');
            }
        } catch (error) {
            console.error('Failed to save role:', error);
            showError('保存失败');
        }
    }

    // ... 其他方法的实现（创建、编辑、删除、查看用户等）
}

// 初始化角色管理器
const roleManager = new RoleManager();

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