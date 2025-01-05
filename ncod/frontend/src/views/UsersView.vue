<template>
    <div class="users">
        <el-card>
            <template #header>
                <div class="card-header">
                    <div class="header-left">
                        <h2>用户管理</h2>
                    </div>
                    <div class="header-right">
                        <el-button type="primary" @click="handleAdd">
                            <el-icon>
                                <Plus />
                            </el-icon>添加用户
                        </el-button>
                        <el-button type="success" @click="handleBatchImport">
                            <el-icon>
                                <Upload />
                            </el-icon>批量导入
                        </el-button>
                        <el-button type="warning" @click="handleBatchExport">
                            <el-icon>
                                <Download />
                            </el-icon>批量导出
                        </el-button>
                    </div>
                </div>
            </template>

            <!-- 搜索和筛选 -->
            <el-form :inline="true" :model="searchForm" class="search-form">
                <el-form-item label="用户名">
                    <el-input v-model="searchForm.username" placeholder="请输入用户名" clearable />
                </el-form-item>
                <el-form-item label="角色">
                    <el-select v-model="searchForm.role" placeholder="请选择角色" clearable>
                        <el-option v-for="role in roles" :key="role.value" :label="role.label" :value="role.value" />
                    </el-select>
                </el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
                        <el-option v-for="status in userStatus" :key="status.value" :label="status.label"
                            :value="status.value" />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">
                        <el-icon>
                            <Search />
                        </el-icon>搜索
                    </el-button>
                    <el-button @click="handleReset">
                        <el-icon>
                            <Refresh />
                        </el-icon>重置
                    </el-button>
                </el-form-item>
            </el-form>

            <!-- 用户列表 -->
            <el-table v-loading="loading" :data="users" style="width: 100%" @selection-change="handleSelectionChange">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="username" label="用户名" min-width="120" />
                <el-table-column prop="realName" label="姓名" width="120" />
                <el-table-column prop="role" label="角色" width="120">
                    <template #default="{ row }">
                        <el-tag>{{ getRoleName(row.role) }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="department" label="部门" width="150" />
                <el-table-column prop="email" label="邮箱" min-width="180" />
                <el-table-column prop="phone" label="电话" width="120" />
                <el-table-column prop="status" label="状态" width="100">
                    <template #default="{ row }">
                        <el-tag :type="getStatusType(row.status)">
                            {{ getStatusName(row.status) }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="lastLogin" label="最后登录" width="180" />
                <el-table-column label="操作" width="200" fixed="right">
                    <template #default="{ row }">
                        <el-button-group>
                            <el-button type="primary" link @click="handleEdit(row)">
                                编辑
                            </el-button>
                            <el-button type="success" link @click="handleResetPassword(row)">
                                重置密码
                            </el-button>
                            <el-button type="danger" link @click="handleDelete(row)" v-if="row.username !== 'admin'">
                                删除
                            </el-button>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination">
                <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
                    :page-sizes="[10, 20, 50, 100]" :total="total" layout="total, sizes, prev, pager, next, jumper"
                    @size-change="handleSizeChange" @current-change="handleCurrentChange" />
            </div>
        </el-card>

        <!-- 添加/编辑用户对话框 -->
        <el-dialog v-model="dialogVisible" :title="dialogType === 'add' ? '添加用户' : '编辑用户'" width="600px">
            <el-form ref="userForm" :model="userFormData" :rules="rules" label-width="100px">
                <el-form-item label="用户名" prop="username">
                    <el-input v-model="userFormData.username" placeholder="请输入用户名" :disabled="dialogType === 'edit'" />
                </el-form-item>
                <el-form-item label="姓名" prop="realName">
                    <el-input v-model="userFormData.realName" placeholder="请输入姓名" />
                </el-form-item>
                <el-form-item label="角色" prop="role">
                    <el-select v-model="userFormData.role" placeholder="请选择角色">
                        <el-option v-for="role in roles" :key="role.value" :label="role.label" :value="role.value" />
                    </el-select>
                </el-form-item>
                <el-form-item label="部门" prop="department">
                    <el-cascader v-model="userFormData.department" :options="departments" placeholder="请选择部门"
                        clearable />
                </el-form-item>
                <el-form-item label="邮箱" prop="email">
                    <el-input v-model="userFormData.email" placeholder="请输入邮箱" />
                </el-form-item>
                <el-form-item label="电话" prop="phone">
                    <el-input v-model="userFormData.phone" placeholder="请输入电话" />
                </el-form-item>
                <el-form-item label="状态" prop="status">
                    <el-switch v-model="userFormData.status" :active-value="'active'" :inactive-value="'inactive'"
                        active-text="启用" inactive-text="禁用" />
                </el-form-item>
                <el-form-item label="备注" prop="remark">
                    <el-input v-model="userFormData.remark" type="textarea" placeholder="请输入备注信息" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleSubmit">确定</el-button>
                </span>
            </template>
        </el-dialog>

        <!-- 重置密码对话框 -->
        <el-dialog v-model="resetPasswordVisible" title="重置密码" width="400px">
            <el-form ref="passwordForm" :model="passwordFormData" :rules="passwordRules" label-width="100px">
                <el-form-item label="新密码" prop="password">
                    <el-input v-model="passwordFormData.password" type="password" placeholder="请输入新密码" show-password />
                </el-form-item>
                <el-form-item label="确认密码" prop="confirmPassword">
                    <el-input v-model="passwordFormData.confirmPassword" type="password" placeholder="请再次输入新密码"
                        show-password />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="resetPasswordVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleResetPasswordSubmit">
                        确定
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Plus, Upload, Download, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'

// 角色选项
const roles = [
    { value: 'admin', label: '管理员' },
    { value: 'manager', label: '部门经理' },
    { value: 'user', label: '普通用户' }
]

// 用户状态选项
const userStatus = [
    { value: 'active', label: '启用' },
    { value: 'inactive', label: '禁用' }
]

// 部门数据
const departments = [
    {
        value: 'tech',
        label: '技术部',
        children: [
            { value: 'dev', label: '研发组' },
            { value: 'test', label: '测试组' },
            { value: 'ops', label: '运维组' }
        ]
    },
    {
        value: 'business',
        label: '业务部',
        children: [
            { value: 'sales', label: '销售组' },
            { value: 'market', label: '市场组' }
        ]
    }
]

// 搜索表单
const searchForm = ref({
    username: '',
    role: '',
    status: ''
})

// 用户表单
const userFormData = ref({
    username: '',
    realName: '',
    role: '',
    department: '',
    email: '',
    phone: '',
    status: 'active',
    remark: ''
})

// 密码表单
const passwordFormData = ref({
    password: '',
    confirmPassword: ''
})

// 表单校验规则
const rules = {
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
    ],
    realName: [
        { required: true, message: '请输入姓名', trigger: 'blur' }
    ],
    role: [
        { required: true, message: '请选择角色', trigger: 'change' }
    ],
    email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
    ],
    phone: [
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
    ]
}

// 密码校验规则
const passwordRules = {
    password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能小于6位', trigger: 'blur' }
    ],
    confirmPassword: [
        { required: true, message: '请再次输入新密码', trigger: 'blur' },
        {
            validator: (rule: any, value: string, callback: Function) => {
                if (value !== passwordFormData.value.password) {
                    callback(new Error('两次输入的密码不一致'))
                } else {
                    callback()
                }
            },
            trigger: 'blur'
        }
    ]
}

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 其他状态
const loading = ref(false)
const dialogVisible = ref(false)
const resetPasswordVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const userForm = ref<FormInstance>()
const passwordForm = ref<FormInstance>()
const selectedUsers = ref<any[]>([])
const currentUser = ref<any>(null)

// 模拟数据
const users = ref([
    {
        username: 'admin',
        realName: '系统管理员',
        role: 'admin',
        department: ['tech', 'dev'],
        email: 'admin@example.com',
        phone: '13800138000',
        status: 'active',
        lastLogin: '2024-01-20 12:00:00'
    },
    {
        username: 'manager',
        realName: '部门经理',
        role: 'manager',
        department: ['business', 'sales'],
        email: 'manager@example.com',
        phone: '13800138001',
        status: 'active',
        lastLogin: '2024-01-20 11:30:00'
    }
])

// 方法
const handleSearch = () => {
    // 实现搜索逻辑
    console.log('搜索条件:', searchForm.value)
}

const handleReset = () => {
    searchForm.value = {
        username: '',
        role: '',
        status: ''
    }
}

const handleAdd = () => {
    dialogType.value = 'add'
    userFormData.value = {
        username: '',
        realName: '',
        role: '',
        department: '',
        email: '',
        phone: '',
        status: 'active',
        remark: ''
    }
    dialogVisible.value = true
}

const handleEdit = (row: any) => {
    dialogType.value = 'edit'
    userFormData.value = { ...row }
    dialogVisible.value = true
}

const handleDelete = (row: any) => {
    ElMessageBox.confirm(
        '确定要删除该用户吗？',
        '警告',
        {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        }
    ).then(() => {
        // 实现删除逻辑
        ElMessage.success('删除成功')
    }).catch(() => {
        // 取消删除
    })
}

const handleResetPassword = (row: any) => {
    currentUser.value = row
    passwordFormData.value = {
        password: '',
        confirmPassword: ''
    }
    resetPasswordVisible.value = true
}

const handleBatchImport = () => {
    // 实现批量导入逻辑
    console.log('批量导入')
}

const handleBatchExport = () => {
    // 实现批量导出逻辑
    console.log('批量导出')
}

const handleSelectionChange = (selection: any[]) => {
    selectedUsers.value = selection
}

const handleSizeChange = (val: number) => {
    pageSize.value = val
    // 重新加载数据
}

const handleCurrentChange = (val: number) => {
    currentPage.value = val
    // 重新加载数据
}

const handleSubmit = async () => {
    if (!userForm.value) return

    await userForm.value.validate((valid: boolean) => {
        if (valid) {
            // 实现提交逻辑
            ElMessage.success(dialogType.value === 'add' ? '添加成功' : '修改成功')
            dialogVisible.value = false
        }
    })
}

const handleResetPasswordSubmit = async () => {
    if (!passwordForm.value) return

    await passwordForm.value.validate((valid: boolean) => {
        if (valid) {
            // 实现重置密码逻辑
            ElMessage.success('密码重置成功')
            resetPasswordVisible.value = false
        }
    })
}

const getRoleName = (role: string) => {
    const found = roles.find(r => r.value === role)
    return found ? found.label : role
}

const getStatusType = (status: string) => {
    return status === 'active' ? 'success' : 'info'
}

const getStatusName = (status: string) => {
    return status === 'active' ? '启用' : '禁用'
}
</script>

<style scoped>
.users {
    padding: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-left h2 {
    margin: 0;
    font-size: 20px;
}

.header-right {
    display: flex;
    gap: 10px;
}

.search-form {
    margin-bottom: 20px;
    padding: 20px;
    background-color: #f5f7fa;
    border-radius: 4px;
}

.pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}

:deep(.el-dialog__body) {
    padding: 20px 40px;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}
</style>