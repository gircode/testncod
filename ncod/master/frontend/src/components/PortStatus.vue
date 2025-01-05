<template>
  <div class="port-status">
    <el-table :data="ports" style="width: 100%">
      <el-table-column prop="port_number" label="端口号" width="100" />
      <el-table-column prop="type" label="端口类型" width="120">
        <template #default="scope">
          {{ getPortType(scope.row.type) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getPortStatusType(scope.row.status)">
            {{ getPortStatusText(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="device_connected" label="已连接设备" />
      <el-table-column prop="last_active" label="最后活动时间">
        <template #default="scope">
          {{ formatDateTime(scope.row.last_active) }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPortStatus } from '@/api/monitor'
import { formatDateTime } from '@/utils/format'
import { ElMessage } from 'element-plus'

const props = defineProps({
  deviceId: {
    type: Number,
    required: true
  }
})

const ports = ref([])

const getPortType = (type) => {
  const types = {
    usb: 'USB',
    serial: '串口',
    network: '网络'
  }
  return types[type] || type
}

const getPortStatusType = (status) => {
  const types = {
    active: 'success',
    inactive: 'info',
    disabled: 'danger'
  }
  return types[status] || 'info'
}

const getPortStatusText = (status) => {
  const texts = {
    active: '活动',
    inactive: '空闲',
    disabled: '禁用'
  }
  return texts[status] || status
}

const fetchPortStatus = async () => {
  try {
    const response = await getPortStatus(props.deviceId)
    ports.value = response.data
  } catch (error) {
    console.error('获取端口状态失败:', error)
    ElMessage.error('获取端口状态失败')
  }
}

onMounted(() => {
  fetchPortStatus()
})

defineExpose({
  refresh: fetchPortStatus
})
</script> 