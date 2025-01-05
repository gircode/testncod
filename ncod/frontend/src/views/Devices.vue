<template>
  <div class="devices-container">
    <el-card>
      <template #header>
        <div class="header-content">
          <h2>设备管理</h2>
          <el-button type="primary" @click="refreshDevices">
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="devices" v-loading="loading">
        <el-table-column prop="name" label="设备名称" />
        <el-table-column prop="type" label="设备类型" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="connected_user" label="使用者" />
        <el-table-column prop="last_seen" label="最后在线时间">
          <template #default="{ row }">
            {{ formatDateTime(row.last_seen) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'online'"
              type="primary" 
              size="small"
              @click="handleConnect(row)"
            >
              连接
            </el-button>
            <el-button 
              v-if="row.status === 'in_use'"
              type="danger" 
              size="small"
              @click="handleRelease(row)"
            >
              释放
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <device-connector
      v-if="selectedDevice"
      v-model:visible="showConnector"
      :device="selectedDevice"
      @connected="handleConnected"
      @failed="handleConnectionFailed"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '@/store/device'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/utils/date'
import DeviceConnector from '@/components/DeviceConnector.vue'

const deviceStore = useDeviceStore()
const devices = ref([])
const loading = ref(false)
const selectedDevice = ref(null)
const showConnector = ref(false)

const getStatusType = (status) => {
  const types = {
    'online': 'success',
    'offline': 'info',
    'in_use': 'warning'
  }
  return types[status] || 'info'
}

const refreshDevices = async () => {
  try {
    loading.value = true
    devices.value = await deviceStore.fetchDevices()
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

const handleConnect = (device) => {
  selectedDevice.value = device
  showConnector.value = true
}

const handleConnected = () => {
  refreshDevices()
}

const handleConnectionFailed = (error) => {
  console.error('Connection failed:', error)
}

const handleRelease = async (device) => {
  try {
    await ElMessageBox.confirm(`确定要释放设备 ${device.name} 吗？`)
    await deviceStore.releaseDevice(device.id)
    ElMessage.success('设备释放成功')
    await refreshDevices()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('设备释放失败')
    }
  }
}

onMounted(() => {
  refreshDevices()
})
</script>

<style scoped>
.devices-container {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 