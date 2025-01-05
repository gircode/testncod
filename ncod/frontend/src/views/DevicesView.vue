<template>
    <div class="devices">
        <el-card>
            <template #header>
                <div class="card-header">
                    <div class="header-left">
                        <h2>设备管理</h2>
                    </div>
                    <div class="header-right">
                        <el-button type="primary" @click="handleAdd">
                            <el-icon>
                                <Plus />
                            </el-icon>添加设备
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
                <el-form-item label="设备名称">
                    <el-input v-model="searchForm.name" placeholder="请输入设备名称" clearable />
                </el-form-item>
                <el-form-item label="设备类型">
                    <el-select v-model="searchForm.type" placeholder="请选择设备类型" clearable>
                        <el-option v-for="type in deviceTypes" :key="type.value" :label="type.label"
                            :value="type.value" />
                    </el-select>
                </el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
                        <el-option v-for="status in deviceStatus" :key="status.value" :label="status.label"
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

            <!-- 设备列表 -->
            <el-table v-loading="loading" :data="devices" style="width: 100%" @selection-change="handleSelectionChange">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="name" label="设备名称" min-width="120" />
                <el-table-column prop="type" label="设备类型" width="120">
                    <template #default="{ row }">
                        <el-tag>{{ getDeviceTypeName(row.type) }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="ip" label="IP地址" width="140" />
                <el-table-column prop="mac" label="MAC地址" width="160" />
                <el-table-column prop="status" label="状态" width="100">
                    <template #default="{ row }">
                        <el-tag :type="getStatusType(row.status)">
                            {{ getStatusName(row.status) }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="lastOnline" label="最后在线" width="180" />
                <el-table-column label="操作" width="200" fixed="right">
                    <template #default="{ row }">
                        <el-button-group>
                            <el-button type="primary" link @click="handleEdit(row)">
                                编辑
                            </el-button>
                            <el-button type="success" link @click="handleDetail(row)">
                                详情
                            </el-button>
                            <el-button type="danger" link @click="handleDelete(row)">
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

        <!-- 添加/编辑设备对话框 -->
        <el-dialog v-model="dialogVisible" :title="dialogType === 'add' ? '添加设备' : '编辑设备'" width="600px">
            <el-form ref="deviceForm" :model="deviceFormData" :rules="rules" label-width="100px">
                <el-form-item label="设备名称" prop="name">
                    <el-input v-model="deviceFormData.name" placeholder="请输入设备名称" />
                </el-form-item>
                <el-form-item label="设备类型" prop="type">
                    <el-select v-model="deviceFormData.type" placeholder="请选择设备类型">
                        <el-option v-for="type in deviceTypes" :key="type.value" :label="type.label"
                            :value="type.value" />
                    </el-select>
                </el-form-item>
                <el-form-item label="IP地址" prop="ip">
                    <el-input v-model="deviceFormData.ip" placeholder="请输入IP地址" />
                </el-form-item>
                <el-form-item label="MAC地址" prop="mac">
                    <el-input v-model="deviceFormData.mac" placeholder="请输入MAC地址" />
                </el-form-item>
                <el-form-item label="备注" prop="remark">
                    <el-input v-model="deviceFormData.remark" type="textarea" placeholder="请输入备注信息" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleSubmit">确定</el-button>
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

// 设备类型选项
const deviceTypes = [
    { value: 'router', label: '路由器' },
    { value: 'switch', label: '交换机' },
    { value: 'firewall', label: '防火墙' },
    { value: 'server', label: '服务器' },
    { value: 'other', label: '其他' }
]

// 设备状态选项
const deviceStatus = [
    { value: 'online', label: '在线' },
    { value: 'offline', label: '离线' },
    { value: 'warning', label: '警告' },
    { value: 'error', label: '故障' }
]

// 搜索表单
const searchForm = ref({
    name: '',
    type: '',
    status: ''
})

// 设备表单
const deviceFormData = ref({
    name: '',
    type: '',
    ip: '',
    mac: '',
    remark: ''
})

// 表单校验规则
const rules = {
    name: [
        { required: true, message: '请输入设备名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    type: [
        { required: true, message: '请选择设备类型', trigger: 'change' }
    ],
    ip: [
        { required: true, message: '请输入IP地址', trigger: 'blur' },
        { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
    ],
    mac: [
        { required: true, message: '请输入MAC地址', trigger: 'blur' },
        { pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, message: 'MAC地址格式不正确', trigger: 'blur' }
    ]
}

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 其他状态
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const deviceForm = ref<FormInstance>()
const selectedDevices = ref<any[]>([])

// 模拟数据
const devices = ref([
    {
        id: 1,
        name: 'Router-001',
        type: 'router',
        ip: '192.168.1.1',
        mac: '00:11:22:33:44:55',
        status: 'online',
        lastOnline: '2024-01-20 12:00:00'
    },
    {
        id: 2,
        name: 'Switch-001',
        type: 'switch',
        ip: '192.168.1.2',
        mac: '00:11:22:33:44:66',
        status: 'warning',
        lastOnline: '2024-01-20 11:30:00'
    }
])

// 方法
const handleSearch = () => {
    // 实现搜索逻辑
    console.log('搜索条件:', searchForm.value)
}

const handleReset = () => {
    searchForm.value = {
        name: '',
        type: '',
        status: ''
    }
}

const handleAdd = () => {
    dialogType.value = 'add'
    deviceFormData.value = {
        name: '',
        type: '',
        ip: '',
        mac: '',
        remark: ''
    }
    dialogVisible.value = true
}

const handleEdit = (row: any) => {
    dialogType.value = 'edit'
    deviceFormData.value = { ...row }
    dialogVisible.value = true
}

const handleDetail = (row: any) => {
    // 实现查看详情逻辑
    console.log('查看设备详情:', row)
}

const handleDelete = (row: any) => {
    ElMessageBox.confirm(
        '确定要删除该设备吗？',
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

const handleBatchImport = () => {
    // 实现批量导入逻辑
    console.log('批量导入')
}

const handleBatchExport = () => {
    // 实现批量导出逻辑
    console.log('批量导出')
}

const handleSelectionChange = (selection: any[]) => {
    selectedDevices.value = selection
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
    if (!deviceForm.value) return

    await deviceForm.value.validate((valid: boolean) => {
        if (valid) {
            // 实现提交逻辑
            ElMessage.success(dialogType.value === 'add' ? '添加成功' : '修改成功')
            dialogVisible.value = false
        }
    })
}

const getDeviceTypeName = (type: string) => {
    const found = deviceTypes.find(t => t.value === type)
    return found ? found.label : type
}

const getStatusType = (status: string) => {
    switch (status) {
        case 'online': return 'success'
        case 'offline': return 'info'
        case 'warning': return 'warning'
        case 'error': return 'danger'
        default: return ''
    }
}

const getStatusName = (status: string) => {
    const statusMap: Record<string, string> = {
        online: '在线',
        offline: '离线',
        warning: '警告',
        error: '故障'
    }
    return statusMap[status] || status
}
</script>

<style scoped>
.devices {
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