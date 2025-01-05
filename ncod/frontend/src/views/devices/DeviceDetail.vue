<template>
  <div class="device-detail">
    <a-card class="device-detail-card">
      <!-- 设备基本信息 -->
      <template #title>
        <div class="card-title">
          <span>设备详情</span>
          <a-space>
            <a-button @click="handleRefresh">
              <template #icon><SyncOutlined /></template>
              刷新
            </a-button>
            <a-button type="primary" @click="handleEdit">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
          </a-space>
        </div>
      </template>

      <a-descriptions bordered>
        <a-descriptions-item label="设备名称">{{ device?.name }}</a-descriptions-item>
        <a-descriptions-item label="设备类型">{{ device?.type }}</a-descriptions-item>
        <a-descriptions-item label="从服务器">{{ device?.slave_name }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="getStatusColor(device?.status)">
            {{ getStatusText(device?.status) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="创建时间">{{ formatDate(device?.created_at) }}</a-descriptions-item>
        <a-descriptions-item label="更新时间">{{ formatDate(device?.updated_at) }}</a-descriptions-item>
        <a-descriptions-item label="描述" :span="3">{{ device?.description || '-' }}</a-descriptions-item>
      </a-descriptions>

      <!-- 设备状态历史 -->
      <a-card class="sub-card" title="状态历史">
        <a-table
          :columns="statusColumns"
          :data-source="statusHistory"
          :loading="loading"
          :pagination="pagination"
          @change="handleTableChange"
        >
          <template #status="{ text }">
            <a-tag :color="getStatusColor(text)">{{ getStatusText(text) }}</a-tag>
          </template>
        </a-table>
      </a-card>

      <!-- 设备使用记录 -->
      <a-card class="sub-card" title="使用记录">
        <a-table
          :columns="usageColumns"
          :data-source="usageHistory"
          :loading="loading"
          :pagination="pagination"
          @change="handleTableChange"
        >
          <template #duration="{ record }">
            {{ formatDuration(record.start_time, record.end_time) }}
          </template>
        </a-table>
      </a-card>
    </a-card>

    <!-- 编辑设备弹窗 -->
    <a-modal
      v-model:visible="modalVisible"
      title="编辑设备"
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
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { TablePaginationConfig } from 'ant-design-vue'
import { SyncOutlined, EditOutlined } from '@ant-design/icons-vue'
import { useDeviceStore } from '@/store/device'
import { formatDate, formatDuration } from '@/utils/format'
import type { Device, DeviceStatus, DeviceUsage, DeviceForm } from '@/types/device'

export default defineComponent({
  name: 'DeviceDetail',
  components: {
    SyncOutlined,
    EditOutlined
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const deviceStore = useDeviceStore()
    const loading = ref(false)
    const device = ref<Device | null>(null)
    const statusHistory = ref<DeviceStatus[]>([])
    const usageHistory = ref<DeviceUsage[]>([])
    const modalVisible = ref(false)
    const deviceFormRef = ref()

    // 设备表单
    const deviceForm = reactive<DeviceForm>({
      name: '',
      type: '',
      slave_id: undefined,
      description: ''
    })

    // 设备类型选项
    const deviceTypes = [
      { value: 'usb', label: 'USB设备' },
      { value: 'serial', label: '串口设备' },
      { value: 'network', label: '网络设备' }
    ]

    // 从服务器列表
    const slaveList = ref([])

    // 分页配置
    const pagination = reactive({
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true
    })

    // 状态历史表格列
    const statusColumns = [
      { title: '状态', dataIndex: 'status', key: 'status', slots: { customRender: 'status' } },
      { title: 'CPU使用率', dataIndex: 'cpu_usage', key: 'cpu_usage' },
      { title: '内存使用率', dataIndex: 'memory_usage', key: 'memory_usage' },
      { title: '磁盘使用率', dataIndex: 'disk_usage', key: 'disk_usage' },
      { title: '记录时间', dataIndex: 'recorded_at', key: 'recorded_at' }
    ]

    // 使用记录表格列
    const usageColumns = [
      { title: '用户', dataIndex: 'user_name', key: 'user_name' },
      { title: '开始时间', dataIndex: 'start_time', key: 'start_time' },
      { title: '结束时间', dataIndex: 'end_time', key: 'end_time' },
      { title: '使用时长', key: 'duration', slots: { customRender: 'duration' } },
      { title: '描述', dataIndex: 'description', key: 'description' }
    ]

    // 表单验证规则
    const rules = {
      name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
      type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
      slave_id: [{ required: true, message: '请选择从服务器', trigger: 'change' }]
    }

    // 获取设备详情
    const fetchDeviceDetail = async () => {
      try {
        loading.value = true
        const deviceId = parseInt(route.params.id as string)
        const data = await deviceStore.getDeviceDetail(deviceId)
        device.value = data
      } catch (error) {
        message.error('获取设备详情失败')
      } finally {
        loading.value = false
      }
    }

    // 获取状态历史
    const fetchStatusHistory = async () => {
      try {
        const deviceId = parseInt(route.params.id as string)
        const params = {
          page: pagination.current,
          pageSize: pagination.pageSize
        }
        const data = await deviceStore.getDeviceStatusHistory(deviceId, params)
        statusHistory.value = data.data
        pagination.total = data.total || 0
      } catch (error) {
        message.error('获取状态历史失败')
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

    // 刷新
    const handleRefresh = () => {
      fetchDeviceDetail()
      fetchStatusHistory()
    }

    // 编辑
    const handleEdit = () => {
      if (device.value) {
        Object.assign(deviceForm, device.value)
        modalVisible.value = true
      }
    }

    // 表格变化
    const handleTableChange = (pag: TablePaginationConfig) => {
      pagination.current = pag.current || 1
      pagination.pageSize = pag.pageSize || 10
      fetchStatusHistory()
    }

    // 弹窗确认
    const handleModalOk = async () => {
      try {
        await deviceFormRef.value.validate()
        const deviceId = parseInt(route.params.id as string)
        await deviceStore.updateDevice(deviceId, deviceForm)
        message.success('更新成功')
        modalVisible.value = false
        fetchDeviceDetail()
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
      fetchDeviceDetail()
      fetchStatusHistory()
      fetchSlaveList()
    })

    return {
      loading,
      device,
      statusHistory,
      usageHistory,
      modalVisible,
      deviceForm,
      deviceFormRef,
      deviceTypes,
      slaveList,
      pagination,
      statusColumns,
      usageColumns,
      rules,
      handleRefresh,
      handleEdit,
      handleTableChange,
      handleModalOk,
      handleModalCancel,
      getStatusColor,
      getStatusText,
      formatDate,
      formatDuration
    }
  }
})
</script>

<style scoped>
.device-detail {
  padding: 24px;
}

.device-detail-card {
  background: #fff;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sub-card {
  margin-top: 24px;
}
</style>