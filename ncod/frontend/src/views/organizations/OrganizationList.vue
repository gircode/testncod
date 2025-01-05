<template>
    <div class="org-list">
        <el-card>
            <template #header>
                <div class="card-header">
                    <div class="header-left">
                        <h2>组织架构管理</h2>
                    </div>
                    <div class="header-right">
                        <el-button-group>
                            <el-button type="primary" @click="() => showAddDialog()" :icon="Plus">
                                添加组织
                            </el-button>
                            <el-button :loading="loading" @click="loadOrganizations" :icon="Refresh">
                                刷新
                            </el-button>
                        </el-button-group>
                    </div>
                </div>
            </template>

            <div class="table-container">
                <el-table 
                    v-loading="loading" 
                    :data="orgList" 
                    row-key="id" 
                    :tree-props="{ children: 'children' }"
                    border
                    stripe
                    highlight-current-row
                >
                    <el-table-column prop="name" label="名称" min-width="150" />
                    <el-table-column prop="code" label="编码" min-width="120" />
                    <el-table-column prop="type" label="类型" width="120">
                        <template #default="{ row }">
                            <el-tag :type="getOrgTypeTag(row.type)">
                                {{ getOrgTypeName(row.type) }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
                    <el-table-column label="操作" width="280" fixed="right">
                        <template #default="{ row }">
                            <el-button-group>
                                <el-tooltip content="添加子组织" placement="top">
                                    <el-button type="primary" @click="showAddDialog(row)" :icon="Plus" />
                                </el-tooltip>
                                <el-tooltip content="编辑组织" placement="top">
                                    <el-button type="primary" @click="showEditDialog(row)" :icon="Edit" />
                                </el-tooltip>
                                <el-tooltip content="删除组织" placement="top">
                                    <el-button type="danger" @click="handleDelete(row)" :icon="Delete" />
                                </el-tooltip>
                            </el-button-group>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
        </el-card>

        <el-dialog
            v-model="dialogVisible"
            :title="dialogTitle"
            width="500px"
            :close-on-click-modal="false"
            destroy-on-close
        >
            <el-form
                ref="formRef"
                :model="form"
                :rules="formRules"
                label-width="100px"
                @submit.prevent="handleSubmit"
                status-icon
            >
                <el-form-item label="名称" prop="name">
                    <el-input 
                        v-model="form.name" 
                        placeholder="请输入组织名称"
                        maxlength="50"
                        show-word-limit
                        clearable
                    />
                </el-form-item>
                <el-form-item label="编码" prop="code">
                    <el-input 
                        v-model="form.code" 
                        placeholder="请输入组织编码"
                        maxlength="20"
                        show-word-limit
                        clearable
                    />
                </el-form-item>
                <el-form-item label="类型" prop="type">
                    <el-select 
                        v-model="form.type" 
                        style="width: 100%"
                        placeholder="请选择组织类型"
                    >
                        <el-option 
                            v-for="(label, value) in orgTypeOptions" 
                            :key="value" 
                            :label="label" 
                            :value="value"
                        />
                    </el-select>
                </el-form-item>
                <el-form-item label="描述" prop="description">
                    <el-input
                        v-model="form.description"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入组织描述"
                        maxlength="200"
                        show-word-limit
                    />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
                        确定
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Refresh, Warning } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, TagProps } from 'element-plus'

interface Organization {
    id: string
    name: string
    code: string
    type: 'company' | 'department' | 'project'
    description?: string
    parentId?: string
    children?: Organization[]
}

interface OrgForm {
    name: string
    code: string
    type: 'company' | 'department' | 'project'
    description: string
    parentId?: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const currentParent = ref<Organization | null>(null)
const isEdit = ref(false)
const currentOrg = ref<Organization | null>(null)
const dialogTitle = ref('添加组织')

const form = ref<OrgForm>({
    name: '',
    code: '',
    type: 'department',
    description: ''
})

const formRules: FormRules = {
    name: [
        { required: true, message: '请输入名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    code: [
        { required: true, message: '请输入编码', trigger: 'blur' },
        { pattern: /^[A-Za-z0-9_-]+$/, message: '编码只能包含字母、数字、下划线和横线', trigger: 'blur' },
        { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
    ],
    type: [
        { required: true, message: '请选择类型', trigger: 'change' }
    ],
    description: [
        { max: 200, message: '描述不能超过200个字符', trigger: 'blur' }
    ]
}

const orgTypeOptions = {
    company: '公司',
    department: '部门',
    project: '项目组'
} as const

const getOrgTypeTag = (type: string): TagProps['type'] => {
    const tagMap: Record<string, TagProps['type']> = {
        company: 'success',
        department: 'warning',
        project: 'info'
    }
    return tagMap[type] || 'info'
}

const getOrgTypeName = (type: string) => {
    return orgTypeOptions[type as keyof typeof orgTypeOptions] || type
}

const updateDialogTitle = () => {
    if (isEdit.value) {
        dialogTitle.value = '编辑组织'
    } else {
        dialogTitle.value = currentParent.value ? `添加子组织 - ${currentParent.value.name}` : '添加组织'
    }
}

// 模拟数据
const mockOrganizations: Organization[] = [
    {
        id: '1',
        name: '总公司',
        code: 'HQ',
        type: 'company',
        description: '总部',
        children: [
            {
                id: '2',
                name: '研发部',
                code: 'RD',
                type: 'department',
                description: '研发部门',
                children: [
                    {
                        id: '4',
                        name: '前端组',
                        code: 'FE',
                        type: 'project',
                        description: '前端开发团队'
                    },
                    {
                        id: '5',
                        name: '后端组',
                        code: 'BE',
                        type: 'project',
                        description: '后端开发团队'
                    }
                ]
            },
            {
                id: '3',
                name: '运维部',
                code: 'OPS',
                type: 'department',
                description: '运维部门'
            }
        ]
    }
]

const orgList = ref<Organization[]>(mockOrganizations)

const loadOrganizations = async () => {
    loading.value = true
    try {
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        orgList.value = mockOrganizations
        ElMessage.success('加载成功')
    } catch (error) {
        ElMessage.error('加载失败')
        console.error(error)
    } finally {
        loading.value = false
    }
}

const showAddDialog = (parent?: Organization | null) => {
    isEdit.value = false
    currentParent.value = parent || null
    form.value = {
        name: '',
        code: '',
        type: parent ? 'department' : 'company',
        description: '',
        parentId: parent?.id
    }
    updateDialogTitle()
    dialogVisible.value = true
}

const showEditDialog = (org: Organization) => {
    isEdit.value = true
    currentOrg.value = org
    form.value = {
        name: org.name,
        code: org.code,
        type: org.type,
        description: org.description || '',
        parentId: org.parentId
    }
    updateDialogTitle()
    dialogVisible.value = true
}

const handleSubmit = async () => {
    if (!formRef.value) return
    
    await formRef.value.validate(async (valid) => {
        if (valid) {
            submitLoading.value = true
            try {
                // 模拟API延迟
                await new Promise(resolve => setTimeout(resolve, 500))
                
                if (isEdit.value && currentOrg.value) {
                    // 编辑现有组织
                    Object.assign(currentOrg.value, {
                        ...form.value,
                        id: currentOrg.value.id
                    })
                } else {
                    // 添加新组织
                    const newOrg: Organization = {
                        id: String(Date.now()),
                        ...form.value
                    }
                    
                    if (currentParent.value) {
                        // 添加为子组织
                        if (!currentParent.value.children) {
                            currentParent.value.children = []
                        }
                        currentParent.value.children.push(newOrg)
                    } else {
                        // 添加为顶级组织
                        orgList.value.push(newOrg)
                    }
                }
                
                ElMessage.success(isEdit.value ? '编辑成功' : '添加成功')
                dialogVisible.value = false
                await loadOrganizations()
            } catch (error) {
                ElMessage.error(isEdit.value ? '编辑失败' : '添加失败')
                console.error(error)
            } finally {
                submitLoading.value = false
            }
        }
    })
}

const handleDelete = async (org: Organization) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除组织 "${org.name}" 吗？${org.children?.length ? '该操作将同时删除所有子组织！' : ''}`,
            '确认删除',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
                icon: Warning
            }
        )
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // 递归查找并删除组织
        const removeOrg = (list: Organization[], id: string): boolean => {
            for (let i = 0; i < list.length; i++) {
                if (list[i].id === id) {
                    list.splice(i, 1)
                    return true
                }
                if (list[i].children) {
                    const children = list[i].children
                    if (children && children.length > 0 && removeOrg(children, id)) {
                        return true
                    }
                }
            }
            return false
        }
        
        removeOrg(orgList.value, org.id)
        ElMessage.success('删除成功')
    } catch (error) {
        if (error !== 'cancel') {
            ElMessage.error('删除失败')
            console.error(error)
        }
    }
}

onMounted(() => {
    loadOrganizations()
})
</script>

<style scoped>
.org-list {
    padding: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-left h2 {
    margin: 0;
    font-size: 18px;
    color: var(--el-text-color-primary);
}

.header-right {
    display: flex;
    gap: 10px;
}

.table-container {
    margin-top: 20px;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

:deep(.el-tag) {
    text-transform: uppercase;
}

:deep(.el-button-group .el-button--primary) {
    --el-button-hover-text-color: var(--el-color-white);
    --el-button-hover-bg-color: var(--el-color-primary-light-3);
    --el-button-hover-border-color: var(--el-color-primary-light-3);
}

:deep(.el-button-group .el-button--danger) {
    --el-button-hover-text-color: var(--el-color-white);
    --el-button-hover-bg-color: var(--el-color-danger-light-3);
    --el-button-hover-border-color: var(--el-color-danger-light-3);
}
</style> 