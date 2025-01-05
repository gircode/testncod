<template>
    <div class="approval-list">
        <el-card>
            <template #header>
                <div class="card-header">
                    <div class="header-left">
                        <h2>用户审批</h2>
                    </div>
                    <div class="header-right">
                        <el-button-group>
                            <el-button :loading="loading" @click="loadApprovals" :icon="Refresh">
                                刷新
                            </el-button>
                            <el-button @click="handleExport" :icon="Download">
                                导出记录
                            </el-button>
                        </el-button-group>
                    </div>
                </div>
            </template>

            <div class="filter-container">
                <el-form :inline="true" :model="filterForm">
                    <el-form-item label="用户名">
                        <el-input
                            v-model="filterForm.username"
                            placeholder="请输入用户名"
                            clearable
                            @keyup.enter="handleFilter"
                        />
                    </el-form-item>
                    <el-form-item label="组织">
                        <el-input
                            v-model="filterForm.organization"
                            placeholder="请输入组织名称"
                            clearable
                            @keyup.enter="handleFilter"
                        />
                    </el-form-item>
                    <el-form-item label="设备类型">
                        <el-select v-model="filterForm.deviceType" placeholder="请选择设备类型" clearable>
                            <el-option
                                v-for="type in deviceTypes"
                                :key="type.value"
                                :label="type.label"
                                :value="type.value"
                            />
                        </el-select>
                    </el-form-item>
                    <el-form-item label="申请时间">
                        <el-date-picker
                            v-model="filterForm.dateRange"
                            type="daterange"
                            range-separator="至"
                            start-placeholder="开始日期"
                            end-placeholder="结束日期"
                            value-format="YYYY-MM-DD"
                        />
                    </el-form-item>
                    <el-form-item>
                        <el-button-group>
                            <el-button type="primary" @click="handleFilter" :icon="Search">
                                搜索
                            </el-button>
                            <el-button @click="resetFilter" :icon="RefreshRight">
                                重置
                            </el-button>
                        </el-button-group>
                    </el-form-item>
                </el-form>
            </div>

            <el-tabs v-model="activeTab" @tab-click="handleTabClick">
                <el-tab-pane label="待审批" name="pending">
                    <el-table
                        v-loading="loading"
                        :data="filteredApprovals"
                        border
                        stripe
                        highlight-current-row
                    >
                        <el-table-column prop="id" label="ID" width="80" />
                        <el-table-column prop="username" label="用户名" min-width="120" />
                        <el-table-column prop="organization" label="所属组织" min-width="150" />
                        <el-table-column prop="requestTime" label="申请时间" min-width="180">
                            <template #default="{ row }">
                                {{ formatDateTimeString(row.requestTime) }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="deviceType" label="设备类型" min-width="120" />
                        <el-table-column prop="deviceId" label="设备ID" min-width="120" />
                        <el-table-column prop="reason" label="申请原因" min-width="200" show-overflow-tooltip />
                        <el-table-column prop="status" label="状态" width="100">
                            <template #default="{ row }">
                                <el-tag :type="getStatusType(row.status)">
                                    {{ getStatusText(row.status) }}
                                </el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="200" fixed="right">
                            <template #default="{ row }">
                                <el-button-group v-if="row.status === 'pending'">
                                    <el-tooltip content="批准申请" placement="top">
                                        <el-button type="success" @click="handleApprove(row)" :icon="Check" />
                                    </el-tooltip>
                                    <el-tooltip content="拒绝申请" placement="top">
                                        <el-button type="danger" @click="handleReject(row)" :icon="Close" />
                                    </el-tooltip>
                                </el-button-group>
                                <el-tooltip v-else content="查看详情" placement="top">
                                    <el-button type="primary" @click="showDetail(row)" :icon="View" />
                                </el-tooltip>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-tab-pane>
                <el-tab-pane label="已处理" name="processed">
                    <el-table
                        v-loading="loading"
                        :data="filteredApprovals"
                        border
                        stripe
                        highlight-current-row
                    >
                        <el-table-column prop="id" label="ID" width="80" />
                        <el-table-column prop="username" label="用户名" min-width="120" />
                        <el-table-column prop="organization" label="所属组织" min-width="150" />
                        <el-table-column prop="requestTime" label="申请时间" min-width="180">
                            <template #default="{ row }">
                                {{ formatDateTimeString(row.requestTime) }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="deviceType" label="设备类型" min-width="120" />
                        <el-table-column prop="deviceId" label="设备ID" min-width="120" />
                        <el-table-column prop="reason" label="申请原因" min-width="200" show-overflow-tooltip />
                        <el-table-column prop="status" label="状态" width="100">
                            <template #default="{ row }">
                                <el-tag :type="getStatusType(row.status)">
                                    {{ getStatusText(row.status) }}
                                </el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column prop="approver" label="处理人" min-width="120" />
                        <el-table-column prop="approvalTime" label="处理时间" min-width="180">
                            <template #default="{ row }">
                                {{ formatDateTimeString(row.approvalTime) }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="comment" label="处理意见" min-width="200" show-overflow-tooltip />
                        <el-table-column label="操作" width="100" fixed="right">
                            <template #default="{ row }">
                                <el-tooltip content="查看详情" placement="top">
                                    <el-button type="primary" @click="showDetail(row)" :icon="View" />
                                </el-tooltip>
                            </template>
                        </el-table-column>
                    </el-table>

                    <div class="pagination-container">
                        <el-pagination
                            v-model:current-page="currentPage"
                            v-model:page-size="pageSize"
                            :page-sizes="[10, 20, 50, 100]"
                            :total="totalItems"
                            layout="total, sizes, prev, pager, next, jumper"
                            @size-change="handleSizeChange"
                            @current-change="handleCurrentChange"
                        />
                    </div>
                </el-tab-pane>
            </el-tabs>
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
                <el-form-item label="处理意见" prop="comment">
                    <el-input
                        v-model="form.comment"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入处理意见"
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

        <el-dialog
            v-model="detailVisible"
            title="申请详情"
            width="600px"
            destroy-on-close
        >
            <el-descriptions :column="2" border>
                <el-descriptions-item label="ID">{{ currentApproval?.id }}</el-descriptions-item>
                <el-descriptions-item label="用户名">{{ currentApproval?.username }}</el-descriptions-item>
                <el-descriptions-item label="所属组织">{{ currentApproval?.organization }}</el-descriptions-item>
                <el-descriptions-item label="申请时间">{{ formatDateTimeString(currentApproval?.requestTime) }}</el-descriptions-item>
                <el-descriptions-item label="设备类型">{{ currentApproval?.deviceType }}</el-descriptions-item>
                <el-descriptions-item label="设备ID">{{ currentApproval?.deviceId }}</el-descriptions-item>
                <el-descriptions-item label="申请原因" :span="2">{{ currentApproval?.reason }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                    <el-tag :type="getStatusType(currentApproval?.status)">
                        {{ getStatusText(currentApproval?.status) }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="处理人">{{ currentApproval?.approver }}</el-descriptions-item>
                <el-descriptions-item label="处理时间">{{ formatDateTimeString(currentApproval?.approvalTime) }}</el-descriptions-item>
                <el-descriptions-item label="处理意见" :span="2">{{ currentApproval?.comment }}</el-descriptions-item>
            </el-descriptions>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
    Refresh,
    Download,
    Search,
    RefreshRight,
    Check,
    Close,
    View,
    Warning
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules, TagProps } from 'element-plus'
import { formatDateTimeString } from '@/utils/format'

type DateRange = [Date, Date]

interface Approval {
    id: string
    username: string
    organization: string
    requestTime: string
    deviceType: string
    deviceId: string
    reason: string
    status: 'pending' | 'approved' | 'rejected'
    approver?: string
    approvalTime?: string
    comment?: string
}

interface ApprovalForm {
    comment: string
}

interface FilterForm {
    username: string
    organization: string
    deviceType: string
    dateRange: string[] | null
}

const deviceTypes = [
    { label: 'USB存储设备', value: 'storage' },
    { label: 'USB打印机', value: 'printer' },
    { label: 'USB摄像头', value: 'camera' },
    { label: 'USB键盘', value: 'keyboard' },
    { label: 'USB鼠标', value: 'mouse' },
    { label: '其他设备', value: 'other' }
]

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const activeTab = ref('pending')
const currentApproval = ref<Approval | null>(null)
const isApprove = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const totalItems = ref(0)

const form = ref<ApprovalForm>({
    comment: ''
})

const filterForm = ref<FilterForm>({
    username: '',
    organization: '',
    deviceType: '',
    dateRange: null
})

const formRules: FormRules = {
    comment: [
        { required: true, message: '请输入处理意见', trigger: 'blur' },
        { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
    ]
}

const dialogTitle = computed(() => {
    return isApprove.value ? '批准申请' : '拒绝申请'
})

// 模拟数据
const mockApprovals: Approval[] = [
    {
        id: '1',
        username: 'user1',
        organization: '研发部',
        requestTime: '2024-01-15T10:30:00',
        deviceType: 'USB存储设备',
        deviceId: 'USB001',
        reason: '需要传输项目文件',
        status: 'pending'
    },
    {
        id: '2',
        username: 'user2',
        organization: '运维部',
        requestTime: '2024-01-15T09:15:00',
        deviceType: 'USB打印机',
        deviceId: 'PRN001',
        reason: '需要打印文档',
        status: 'approved',
        approver: 'admin',
        approvalTime: '2024-01-15T09:30:00',
        comment: '已确认需求，同意使用'
    },
    {
        id: '3',
        username: 'user3',
        organization: '市场部',
        requestTime: '2024-01-14T16:45:00',
        deviceType: 'USB摄像头',
        deviceId: 'CAM001',
        reason: '需要进行视频会议',
        status: 'rejected',
        approver: 'admin',
        approvalTime: '2024-01-14T17:00:00',
        comment: '请使用公司统一配置的视频设备'
    }
]

const approvalList = ref<Approval[]>(mockApprovals)

const totalFilteredItems = ref(0)
const filteredList = ref<Approval[]>([])

// 更新过滤后的列表
const updateFilteredList = () => {
    let result = approvalList.value

    if (filterForm.value.username) {
        result = result.filter(a => 
            a.username.toLowerCase().includes(filterForm.value.username.toLowerCase())
        )
    }

    if (filterForm.value.organization) {
        result = result.filter(a => 
            a.organization.toLowerCase().includes(filterForm.value.organization.toLowerCase())
        )
    }

    if (filterForm.value.deviceType) {
        result = result.filter(a => a.deviceType === filterForm.value.deviceType)
    }

    if (filterForm.value.dateRange) {
        const [start, end] = filterForm.value.dateRange
        result = result.filter(a => {
            const date = new Date(a.requestTime).toISOString().split('T')[0]
            return date >= start && date <= end
        })
    }

    if (activeTab.value === 'pending') {
        result = result.filter(a => a.status === 'pending')
    } else {
        result = result.filter(a => a.status !== 'pending')
    }

    totalFilteredItems.value = result.length
    filteredList.value = result
}
    
// 计算当前页的数据
const filteredApprovals = computed(() => {
    const startIndex = (currentPage.value - 1) * pageSize.value
    return filteredList.value.slice(startIndex, startIndex + pageSize.value)
})

const handleFilter = () => {
    currentPage.value = 1
    updateFilteredList()
}

const resetFilter = () => {
    filterForm.value = {
        username: '',
        organization: '',
        deviceType: '',
        dateRange: null
    }
    handleFilter()
}

const handleSizeChange = (val: number) => {
    pageSize.value = val
    loadApprovals()
}

const handleCurrentChange = (val: number) => {
    currentPage.value = val
    loadApprovals()
}

const handleExport = () => {
    ElMessage.success('导出成功')
}

const getStatusType = (status?: string): TagProps['type'] => {
    const typeMap: Record<string, TagProps['type']> = {
        pending: 'warning',
        approved: 'success',
        rejected: 'danger'
    }
    return typeMap[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
    const textMap: Record<string, string> = {
        pending: '待审批',
        approved: '已批准',
        rejected: '已拒绝'
    }
    return textMap[status || ''] || status || ''
}

const formatDate = (date?: string) => {
    if (!date) return ''
    return new Date(date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    })
}

const loadApprovals = async () => {
    loading.value = true
    try {
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        approvalList.value = mockApprovals
        ElMessage.success('加载成功')
    } catch (error) {
        ElMessage.error('加载失败')
        console.error(error)
    } finally {
        loading.value = false
    }
}

const handleTabClick = () => {
    loadApprovals()
}

const handleApprove = (approval: Approval) => {
    currentApproval.value = approval
    isApprove.value = true
    form.value.comment = ''
    dialogVisible.value = true
}

const handleReject = (approval: Approval) => {
    currentApproval.value = approval
    isApprove.value = false
    form.value.comment = ''
    dialogVisible.value = true
}

const showDetail = (approval: Approval) => {
    currentApproval.value = approval
    detailVisible.value = true
}

const handleSubmit = async () => {
    if (!formRef.value || !currentApproval.value) return
    
    await formRef.value.validate(async (valid) => {
        if (valid) {
            submitLoading.value = true
            try {
                const approval = currentApproval.value
                if (!approval) return

                // 模拟API延迟
                await new Promise(resolve => setTimeout(resolve, 500))
                
                const updatedApproval: Approval = {
                    id: approval.id,
                    username: approval.username,
                    organization: approval.organization,
                    requestTime: approval.requestTime,
                    deviceType: approval.deviceType,
                    deviceId: approval.deviceId,
                    reason: approval.reason,
                    status: isApprove.value ? 'approved' : 'rejected',
                    approver: 'admin',
                    approvalTime: new Date().toISOString(),
                    comment: form.value.comment
                }
                
                currentApproval.value = updatedApproval
                
                ElMessage.success('处理成功')
                dialogVisible.value = false
                await loadApprovals()
            } catch (error) {
                ElMessage.error('处理失败')
                console.error(error)
            } finally {
                submitLoading.value = false
            }
        }
    })
}

// 自动刷新
let refreshTimer: number | null = null

const startAutoRefresh = () => {
    stopAutoRefresh()
    refreshTimer = window.setInterval(() => {
        loadApprovals()
    }, 30000) // 每30秒刷新一次
}

const stopAutoRefresh = () => {
    if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
    }
}

onMounted(() => {
    loadApprovals()
    startAutoRefresh()
})

onUnmounted(() => {
    stopAutoRefresh()
})
</script>

<style scoped>
.approval-list {
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

.filter-container {
    margin-bottom: 20px;
    padding: 15px;
    background-color: var(--el-fill-color-light);
    border-radius: var(--el-border-radius-base);
}

.pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}

:deep(.el-tag) {
    text-transform: uppercase;
}

:deep(.el-descriptions) {
    padding: 10px;
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

:deep(.el-button-group .el-button--success) {
    --el-button-hover-text-color: var(--el-color-white);
    --el-button-hover-bg-color: var(--el-color-success-light-3);
    --el-button-hover-border-color: var(--el-color-success-light-3);
}
</style> 