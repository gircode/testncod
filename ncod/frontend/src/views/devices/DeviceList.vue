<!-- 设备管理页面 -->
<template>
    <div class="device-list">
        <a-card class="device-list-card" title="设备管理">
            <!-- 搜索表单 -->
            <a-form layout="inline" class="search-form">
                <a-form-item label="设备名称">
                    <a-input v-model:value="searchForm.name" placeholder="请输入设备名称" />
                </a-form-item>
                <a-form-item label="设备类型">
                    <a-select v-model:value="searchForm.type" placeholder="请选择设备类型" style="width: 200px">
                        <a-select-option value="">全部</a-select-option>
                        <a-select-option v-for="type in deviceTypes" :key="type.value" :value="type.value">
                            {{ type.label }}
                        </a-select-option>
                    </a-select>
                </a-form-item>
                <a-form-item label="状态">
                    <a-select v-model:value="searchForm.status" placeholder="请选择状态" style="width: 200px">
                        <a-select-option value="">全部</a-select-option>
                        <a-select-option value="online">在线</a-select-option>
                        <a-select-option value="offline">离线</a-select-option>
                        <a-select-option value="in_use">使用中</a-select-option>
                    </a-select>
                </a-form-item>
                <a-form-item>
                    <a-button type="primary" @click="handleSearch">
                        <template #icon><SearchOutlined /></template>
                        搜索
                    </a-button>
                    <a-button style="margin-left: 8px" @click="handleReset">
                        <template #icon><ReloadOutlined /></template>
                        重置
                    </a-button>
                </a-form-item>
            </a-form>

            <!-- 操作按钮 -->
            <div class="operation-bar">
                <a-button type="primary" @click="handleAdd">
                    <template #icon><PlusOutlined /></template>
                    添加设备
                </a-button>
                <a-button style="margin-left: 8px" @click="handleRefresh">
                    <template #icon><SyncOutlined /></template>
                    刷新
                </a-button>
            </div>

            <!-- 设备列表 -->
            <a-table
                :columns="columns"
                :data-source="deviceList"
                :loading="loading"
                :pagination="pagination"
                @change="handleTableChange"
                row-key="id"
            >
                <!-- 状态列 -->
                <template #status="{ text }">
                    <a-tag :color="getStatusColor(text)">{{ getStatusText(text) }}</a-tag>
                </template>

                <!-- 操作列 -->
                <template #action="{ record }">
                    <a-space>
                        <a-button type="link" @click="handleEdit(record)">编辑</a-button>
                        <a-button type="link" @click="handleView(record)">查看</a-button>
                        <a-popconfirm
                            title="确定要删除这个设备吗？"
                            @confirm="handleDelete(record)"
                            ok-text="确定"
                            cancel-text="取消"
                        >
                            <a-button type="link" danger>删除</a-button>
                        </a-popconfirm>
                    </a-space>
                </template>
            </a-table>

            <!-- 添加/编辑设备弹窗 -->
            <a-modal
                v-model:visible="modalVisible"
                :title="modalTitle"
                @ok="handleModalOk"
                @cancel="handleModalCancel"
            >
                <a-form :model="deviceForm" :rules="rules" ref="deviceFormRef">
                    <a-form-item label="设备名称" name="name">
                        <a-input v-model:value="deviceForm.name" placeholder="请输入设备名称" />
                    </a-form-item>
                    <a-form-item label="设备类型" name="type">
                        <a-select v-model:value="deviceForm.type" placeholder="请选择设备类型">
                            <a-select-option v-for="type in deviceTypes" :key="type.value" :value="type.value">
                                {{ type.label }}
                            </a-select-option>
                        </a-select>
                    </a-form-item>
                    <a-form-item label="从服务器" name="slave_id">
                        <a-select v-model:value="deviceForm.slave_id" placeholder="请选择从服务器">
                            <a-select-option v-for="slave in slaveList" :key="slave.id" :value="slave.id">
                                {{ slave.name }}
                            </a-select-option>
                        </a-select>
                    </a-form-item>
                    <a-form-item label="描述" name="description">
                        <a-textarea v-model:value="deviceForm.description" placeholder="请输入设备描述" />
                    </a-form-item>
                </a-form>
            </a-modal>
        </a-card>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { TablePaginationConfig } from 'ant-design-vue'
import {
    SearchOutlined,
    ReloadOutlined,
    PlusOutlined,
    SyncOutlined,
    EditOutlined,
    DeleteOutlined,
    EyeOutlined
} from '@ant-design/icons-vue'
import { useDeviceStore } from '@/store/device'
import type { Device, DeviceForm, DeviceSearchParams } from '@/types/device'

export default defineComponent({
    name: 'DeviceList',
    components: {
        SearchOutlined,
        ReloadOutlined,
        PlusOutlined,
        SyncOutlined,
        EditOutlined,
        DeleteOutlined,
        EyeOutlined
    },
    setup() {
        const router = useRouter()
        const deviceStore = useDeviceStore()
        const loading = ref(false)
        const modalVisible = ref(false)
        const modalTitle = ref('添加设备')
        const deviceFormRef = ref()

        // 搜索表单
        const searchForm = reactive<DeviceSearchParams>({
            name: '',
            type: '',
            status: ''
        })

        // 设备表单
        const deviceForm = reactive<DeviceForm>({
            name: '',
            type: '',
            slave_id: undefined,
            description: ''
        })

        // 表格列定义
        const columns = [
            {
                title: '设备名称',
                dataIndex: 'name',
                key: 'name'
            },
            {
                title: '设备类型',
                dataIndex: 'type',
                key: 'type'
            },
            {
                title: '从服务器',
                dataIndex: 'slave_name',
                key: 'slave_name'
            },
            {
                title: '状态',
                dataIndex: 'status',
                key: 'status',
                slots: { customRender: 'status' }
            },
            {
                title: '操作',
                key: 'action',
                slots: { customRender: 'action' }
            }
        ]

        // 分页配置
        const pagination = reactive({
            current: 1,
            pageSize: 10,
            total: 0,
            showSizeChanger: true,
            showQuickJumper: true
        })

        // 设备类型选项
        const deviceTypes = [
            { value: 'usb', label: 'USB设备' },
            { value: 'serial', label: '串口设备' },
            { value: 'network', label: '网络设备' }
        ]

        // 从服务器列表
        const slaveList = ref([])

        // 设备列表
        const deviceList = ref<Device[]>([])

        // 表单验证规则
        const rules = {
            name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
            type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
            slave_id: [{ required: true, message: '请选择从服务器', trigger: 'change' }]
        }

        // 获取设备列表
        const fetchDeviceList = async () => {
            try {
                loading.value = true
                const params = {
                    page: pagination.current,
                    pageSize: pagination.pageSize,
                    ...searchForm
                }
                const { data, total } = await deviceStore.getDeviceList(params)
                deviceList.value = data
                pagination.total = total
            } catch (error) {
                message.error('获取设备列表失败')
            } finally {
                loading.value = false
            }
        }

        // 获取从服务器列表
        const fetchSlaveList = async () => {
            try {
                const response = await deviceStore.getSlaveList()
                slaveList.value = response.data
            } catch (error) {
                message.error('获取从服务器列表失败')
            }
        }

        // 搜索
        const handleSearch = () => {
            pagination.current = 1
            fetchDeviceList()
        }

        // 重置搜索
        const handleReset = () => {
            Object.assign(searchForm, {
                name: '',
                type: '',
                status: ''
            })
            handleSearch()
        }

        // 表格变化
        const handleTableChange = (pag: TablePaginationConfig) => {
            pagination.current = pag.current || 1
            pagination.pageSize = pag.pageSize || 10
            fetchDeviceList()
        }

        // 添加设备
        const handleAdd = () => {
            modalTitle.value = '添加设备'
            Object.assign(deviceForm, {
                name: '',
                type: '',
                slave_id: undefined,
                description: ''
            })
            modalVisible.value = true
        }

        // 编辑设备
        const handleEdit = (record: Device) => {
            modalTitle.value = '编辑设备'
            Object.assign(deviceForm, {
                ...record
            })
            modalVisible.value = true
        }

        // 查看设备
        const handleView = (record: Device) => {
            router.push(`/master/devices/${record.id}`)
        }

        // 删除设备
        const handleDelete = async (record: Device) => {
            try {
                await deviceStore.deleteDevice(record.id)
                message.success('删除成功')
                fetchDeviceList()
            } catch (error) {
                message.error('删除失败')
            }
        }

        // 刷新列表
        const handleRefresh = () => {
            fetchDeviceList()
        }

        // 弹窗确认
        const handleModalOk = async () => {
            try {
                await deviceFormRef.value.validate()
                if (modalTitle.value === '添加设备') {
                    await deviceStore.createDevice(deviceForm)
                    message.success('添加成功')
                } else {
                    await deviceStore.updateDevice(deviceForm.id!, deviceForm)
                    message.success('更新成功')
                }
                modalVisible.value = false
                fetchDeviceList()
            } catch (error) {
                // 表单验证失败或请求失败
            }
        }

        // 弹窗取消
        const handleModalCancel = () => {
            modalVisible.value = false
            deviceFormRef.value?.resetFields()
        }

        // 获取状态颜色
        const getStatusColor = (status: string) => {
            const colors: Record<string, string> = {
                online: 'success',
                offline: 'default',
                in_use: 'processing'
            }
            return colors[status] || 'default'
        }

        // 获取状态文本
        const getStatusText = (status: string) => {
            const texts: Record<string, string> = {
                online: '在线',
                offline: '离线',
                in_use: '使用中'
            }
            return texts[status] || status
        }

        onMounted(() => {
            fetchDeviceList()
            fetchSlaveList()
        })

        return {
            loading,
            searchForm,
            deviceForm,
            deviceFormRef,
            columns,
            deviceList,
            pagination,
            modalVisible,
            modalTitle,
            deviceTypes,
            slaveList,
            rules,
            handleSearch,
            handleReset,
            handleTableChange,
            handleAdd,
            handleEdit,
            handleView,
            handleDelete,
            handleRefresh,
            handleModalOk,
            handleModalCancel,
            getStatusColor,
            getStatusText
        }
    }
})
</script>

<style scoped>
.device-list {
    padding: 24px;
}

.device-list-card {
    background: #fff;
}

.search-form {
    margin-bottom: 24px;
}

.operation-bar {
    margin-bottom: 16px;
}
</style>