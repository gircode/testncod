<template>
    <div class="organizations">
        <el-row :gutter="20">
            <!-- 组织树 -->
            <el-col :span="6">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>组织架构</span>
                            <el-button-group>
                                <el-button type="primary" link @click="handleAddOrg">
                                    <el-icon>
                                        <Plus />
                                    </el-icon>
                                </el-button>
                                <el-button type="primary" link @click="handleRefresh">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon>
                                </el-button>
                            </el-button-group>
                        </div>
                    </template>
                    <el-tree ref="orgTree" :data="organizations" :props="defaultProps" node-key="id" default-expand-all
                        highlight-current @node-click="handleNodeClick">
                        <template #default="{ node, data }">
                            <span class="custom-tree-node">
                                <span>{{ node.label }}</span>
                                <span class="actions">
                                    <el-button type="primary" link @click.stop="handleEdit(data)">
                                        编辑
                                    </el-button>
                                    <el-button type="danger" link @click.stop="handleDelete(node, data)"
                                        v-if="data.id !== 'root'">
                                        删除
                                    </el-button>
                                </span>
                            </span>
                        </template>
                    </el-tree>
                </el-card>
            </el-col>

            <!-- 部门详情 -->
            <el-col :span="18">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <span>{{ currentNode ? currentNode.name : '部门详情' }}</span>
                            <div class="header-right" v-if="currentNode">
                                <el-button type="primary" @click="handleAddMember">
                                    <el-icon>
                                        <Plus />
                                    </el-icon>添加成员
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

                    <!-- 部门信息 -->
                    <template v-if="currentNode">
                        <el-descriptions class="margin-bottom" title="基本信息" :column="3" border>
                            <el-descriptions-item label="部门名称">
                                {{ currentNode.name }}
                            </el-descriptions-item>
                            <el-descriptions-item label="部门编码">
                                {{ currentNode.code }}
                            </el-descriptions-item>
                            <el-descriptions-item label="负责人">
                                {{ currentNode.manager }}
                            </el-descriptions-item>
                            <el-descriptions-item label="创建时间">
                                {{ currentNode.createTime }}
                            </el-descriptions-item>
                            <el-descriptions-item label="成员数量">
                                {{ currentNode.memberCount }}
                            </el-descriptions-item>
                            <el-descriptions-item label="状态">
                                <el-tag :type="currentNode.status === 'active' ? 'success' : 'info'">
                                    {{ currentNode.status === 'active' ? '正常' : '禁用' }}
                                </el-tag>
                            </el-descriptions-item>
                        </el-descriptions>

                        <!-- 成员列表 -->
                        <el-table v-loading="loading" :data="members" style="width: 100%"
                            @selection-change="handleSelectionChange">
                            <el-table-column type="selection" width="55" />
                            <el-table-column prop="name" label="姓名" width="120" />
                            <el-table-column prop="position" label="职位" width="120" />
                            <el-table-column prop="email" label="邮箱" min-width="180" />
                            <el-table-column prop="phone" label="电话" width="120" />
                            <el-table-column prop="joinTime" label="加入时间" width="180" />
                            <el-table-column prop="status" label="状态" width="100">
                                <template #default="{ row }">
                                    <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                                        {{ row.status === 'active' ? '在职' : '离职' }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column label="操作" width="200" fixed="right">
                                <template #default="{ row }">
                                    <el-button-group>
                                        <el-button type="primary" link @click="handleEditMember(row)">
                                            编辑
                                        </el-button>
                                        <el-button type="warning" link @click="handleTransfer(row)">
                                            调动
                                        </el-button>
                                        <el-button type="danger" link @click="handleRemoveMember(row)">
                                            移除
                                        </el-button>
                                    </el-button-group>
                                </template>
                            </el-table-column>
                        </el-table>

                        <!-- 分页 -->
                        <div class="pagination">
                            <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
                                :page-sizes="[10, 20, 50, 100]" :total="total"
                                layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange"
                                @current-change="handleCurrentChange" />
                        </div>
                    </template>

                    <!-- 未选择部门时的提示 -->
                    <el-empty v-else description="请选择部门查看详细信息" />
                </el-card>
            </el-col>
        </el-row>

        <!-- 添加/编辑部门对话框 -->
        <el-dialog v-model="orgDialogVisible" :title="dialogType === 'add' ? '添加部门' : '编辑部门'" width="500px">
            <el-form ref="orgForm" :model="orgForm" :rules="orgRules" label-width="100px">
                <el-form-item label="部门名称" prop="name">
                    <el-input v-model="orgForm.name" placeholder="请输入部门名称" />
                </el-form-item>
                <el-form-item label="部门编码" prop="code">
                    <el-input v-model="orgForm.code" placeholder="请输入部门编码" />
                </el-form-item>
                <el-form-item label="负责人" prop="manager">
                    <el-select v-model="orgForm.manager" placeholder="请选择负责人" filterable>
                        <el-option v-for="user in users" :key="user.id" :label="user.name" :value="user.id" />
                    </el-select>
                </el-form-item>
                <el-form-item label="上级部门" prop="parentId">
                    <el-cascader v-model="orgForm.parentId" :options="organizationOptions"
                        :props="{ checkStrictly: true }" clearable placeholder="请选择上级部门" />
                </el-form-item>
                <el-form-item label="状态" prop="status">
                    <el-switch v-model="orgForm.status" :active-value="'active'" :inactive-value="'inactive'"
                        active-text="启用" inactive-text="禁用" />
                </el-form-item>
                <el-form-item label="备注" prop="remark">
                    <el-input v-model="orgForm.remark" type="textarea" placeholder="请输入备注信息" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="orgDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleOrgSubmit">确定</el-button>
                </span>
            </template>
        </el-dialog>

        <!-- 添加/编辑成员对话框 -->
        <el-dialog v-model="memberDialogVisible" :title="dialogType === 'add' ? '添加成员' : '编辑成员'" width="500px">
            <el-form ref="memberForm" :model="memberForm" :rules="memberRules" label-width="100px">
                <el-form-item label="姓名" prop="name">
                    <el-input v-model="memberForm.name" placeholder="请输入姓名" />
                </el-form-item>
                <el-form-item label="职位" prop="position">
                    <el-input v-model="memberForm.position" placeholder="请输入职位" />
                </el-form-item>
                <el-form-item label="邮箱" prop="email">
                    <el-input v-model="memberForm.email" placeholder="请输入邮箱" />
                </el-form-item>
                <el-form-item label="电话" prop="phone">
                    <el-input v-model="memberForm.phone" placeholder="请输入电话" />
                </el-form-item>
                <el-form-item label="状态" prop="status">
                    <el-switch v-model="memberForm.status" :active-value="'active'" :inactive-value="'inactive'"
                        active-text="在职" inactive-text="离职" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="memberDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleMemberSubmit">确定</el-button>
                </span>
            </template>
        </el-dialog>

        <!-- 调动部门对话框 -->
        <el-dialog v-model="transferDialogVisible" title="调动部门" width="400px">
            <el-form ref="transferForm" :model="transferForm" :rules="transferRules" label-width="100px">
                <el-form-item label="目标部门" prop="targetDepartment">
                    <el-cascader v-model="transferForm.targetDepartment" :options="organizationOptions"
                        :props="{ checkStrictly: true }" clearable placeholder="请选择目标部门" />
                </el-form-item>
                <el-form-item label="新职位" prop="newPosition">
                    <el-input v-model="transferForm.newPosition" placeholder="请输入新职位" />
                </el-form-item>
                <el-form-item label="调动原因" prop="reason">
                    <el-input v-model="transferForm.reason" type="textarea" placeholder="请输入调动原因" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="transferDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleTransferSubmit">
                        确定
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Plus, Upload, Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus/es/components/form'
import type { FormRules } from 'element-plus/es/components/form'

// 组织树配置
const defaultProps = {
    children: 'children',
    label: 'name'
}

// 模拟组织数据
const organizations = ref([
    {
        id: 'root',
        name: '总公司',
        code: 'HQ',
        manager: '张三',
        createTime: '2024-01-01',
        memberCount: 150,
        status: 'active',
        children: [
            {
                id: 'tech',
                name: '技术部',
                code: 'TECH',
                manager: '李四',
                createTime: '2024-01-02',
                memberCount: 50,
                status: 'active',
                children: [
                    {
                        id: 'dev',
                        name: '研发组',
                        code: 'DEV',
                        manager: '王五',
                        createTime: '2024-01-03',
                        memberCount: 30,
                        status: 'active'
                    },
                    {
                        id: 'test',
                        name: '测试组',
                        code: 'TEST',
                        manager: '赵六',
                        createTime: '2024-01-03',
                        memberCount: 20,
                        status: 'active'
                    }
                ]
            },
            {
                id: 'business',
                name: '业务部',
                code: 'BIZ',
                manager: '钱七',
                createTime: '2024-01-02',
                memberCount: 100,
                status: 'active',
                children: [
                    {
                        id: 'sales',
                        name: '销售组',
                        code: 'SALES',
                        manager: '孙八',
                        createTime: '2024-01-03',
                        memberCount: 60,
                        status: 'active'
                    },
                    {
                        id: 'market',
                        name: '市场组',
                        code: 'MKT',
                        manager: '周九',
                        createTime: '2024-01-03',
                        memberCount: 40,
                        status: 'active'
                    }
                ]
            }
        ]
    }
])

// 将组织数据转换为级联选择器选项
const organizationOptions = ref(organizations.value.map(org => ({
    value: org.id,
    label: org.name,
    children: org.children?.map(child => ({
        value: child.id,
        label: child.name,
        children: child.children?.map(subChild => ({
            value: subChild.id,
            label: subChild.name
        }))
    }))
})))

// 模拟成员数据
const members = ref([
    {
        id: 1,
        name: '张三',
        position: '总经理',
        email: 'zhangsan@example.com',
        phone: '13800138000',
        joinTime: '2024-01-01',
        status: 'active'
    },
    {
        id: 2,
        name: '李四',
        position: '技术总监',
        email: 'lisi@example.com',
        phone: '13800138001',
        joinTime: '2024-01-02',
        status: 'active'
    }
])

// 模拟用户数据
const users = ref([
    { id: 1, name: '张三' },
    { id: 2, name: '李四' },
    { id: 3, name: '王五' }
])

// 状态变量
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const currentNode = ref<any>(null)
const selectedMembers = ref<any[]>([])

// 对话框相关
const orgDialogVisible = ref(false)
const memberDialogVisible = ref(false)
const transferDialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')

// 表单相关
const orgForm = ref({
    name: '',
    code: '',
    manager: '',
    parentId: '',
    status: 'active',
    remark: ''
})

const memberForm = ref({
    name: '',
    position: '',
    email: '',
    phone: '',
    status: 'active'
})

const transferForm = ref({
    targetDepartment: '',
    newPosition: '',
    reason: ''
})

// 表单校验规则
const orgRules = {
    name: [
        { required: true, message: '请输入部门名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    code: [
        { required: true, message: '请输入部门编码', trigger: 'blur' },
        { pattern: /^[A-Z0-9]+$/, message: '部门编码只能包含大写字母和数字', trigger: 'blur' }
    ],
    manager: [
        { required: true, message: '请选择负责人', trigger: 'change' }
    ]
}

const memberRules = {
    name: [
        { required: true, message: '请输入姓名', trigger: 'blur' }
    ],
    position: [
        { required: true, message: '请输入职位', trigger: 'blur' }
    ],
    email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
    ],
    phone: [
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
    ]
}

const transferRules = {
    targetDepartment: [
        { required: true, message: '请选择目标部门', trigger: 'change' }
    ],
    newPosition: [
        { required: true, message: '请输入新职位', trigger: 'blur' }
    ],
    reason: [
        { required: true, message: '请输入调动原因', trigger: 'blur' }
    ]
}

// 组织树相关方法
const handleNodeClick = (data: any) => {
    currentNode.value = data
    // 加载该部门的成员数据
    loadMembers(data.id)
}

const handleAddOrg = () => {
    dialogType.value = 'add'
    orgForm.value = {
        name: '',
        code: '',
        manager: '',
        parentId: currentNode.value ? currentNode.value.id : '',
        status: 'active',
        remark: ''
    }
    orgDialogVisible.value = true
}

const handleEdit = (data: any) => {
    dialogType.value = 'edit'
    orgForm.value = { ...data }
    orgDialogVisible.value = true
}

const handleDelete = (node: any, data: any) => {
    ElMessageBox.confirm(
        '确定要删除该部门吗？如果存在子部门，将无法删除。',
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

const handleRefresh = () => {
    // 实现刷新组织树的逻辑
}

// 成员相关方法
const loadMembers = (departmentId: string) => {
    loading.value = true
    // 实现加载成员数据的逻辑
    setTimeout(() => {
        loading.value = false
    }, 500)
}

const handleAddMember = () => {
    dialogType.value = 'add'
    memberForm.value = {
        name: '',
        position: '',
        email: '',
        phone: '',
        status: 'active'
    }
    memberDialogVisible.value = true
}

const handleEditMember = (row: any) => {
    dialogType.value = 'edit'
    memberForm.value = { ...row }
    memberDialogVisible.value = true
}

const handleRemoveMember = (row: any) => {
    ElMessageBox.confirm(
        '确定要移除该成员吗？',
        '警告',
        {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        }
    ).then(() => {
        // 实现移除成员的逻辑
        ElMessage.success('移除成功')
    }).catch(() => {
        // 取消移除
    })
}

const handleTransfer = (row: any) => {
    transferForm.value = {
        targetDepartment: '',
        newPosition: row.position,
        reason: ''
    }
    transferDialogVisible.value = true
}

const handleBatchImport = () => {
    // 实现批量导入成员的逻辑
}

const handleBatchExport = () => {
    // 实现批量导出成员的逻辑
}

const handleSelectionChange = (selection: any[]) => {
    selectedMembers.value = selection
}

// 分页方法
const handleSizeChange = (val: number) => {
    pageSize.value = val
    loadMembers(currentNode.value.id)
}

const handleCurrentChange = (val: number) => {
    currentPage.value = val
    loadMembers(currentNode.value.id)
}

// 表单提交方法
const handleOrgSubmit = async () => {
    const form = orgForm.value as unknown as FormInstance
    if (!form) return

    await form.validate((valid: boolean) => {
        if (valid) {
            // 实现提交逻辑
            ElMessage.success(dialogType.value === 'add' ? '添加成功' : '修改成功')
            orgDialogVisible.value = false
        }
    })
}

const handleMemberSubmit = async () => {
    const form = memberForm.value as unknown as FormInstance
    if (!form) return

    await form.validate((valid: boolean) => {
        if (valid) {
            // 实现提交逻辑
            ElMessage.success(dialogType.value === 'add' ? '添加成功' : '修改成功')
            memberDialogVisible.value = false
        }
    })
}

const handleTransferSubmit = async () => {
    const form = transferForm.value as unknown as FormInstance
    if (!form) return

    await form.validate((valid: boolean) => {
        if (valid) {
            // 实现调动逻辑
            ElMessage.success('调动成功')
            transferDialogVisible.value = false
        }
    })
}
</script>

<style scoped>
.organizations {
    padding: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-right {
    display: flex;
    gap: 10px;
}

.custom-tree-node {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    padding-right: 8px;
}

.actions {
    display: none;
}

.el-tree-node:hover .actions {
    display: inline-flex;
    gap: 8px;
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

.margin-bottom {
    margin-bottom: 20px;
}
</style>