<template>
  <div class="slave-detail">
    <!-- 基本信息卡片 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <h3>基本信息</h3>
            <el-tag :type="slave?.isActive ? 'success' : 'danger'">
              {{ slave?.isActive ? '在线' : '离线' }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button type="primary" @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="handleBack">
              <el-icon><Back /></el-icon>
              返回
            </el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="服务器名称">
          <div class="slave-name">
            <el-icon :size="20" :class="slave?.isActive ? 'online' : 'offline'">
              <Monitor />
            </el-icon>
            <span>{{ slave?.name }}</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="主机地址">
          {{ slave?.host }}:{{ slave?.port }}
        </el-descriptions-item>
        <el-descriptions-item label="设备数量">
          <el-tag type="info">{{ slave?.deviceCount || 0 }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(slave?.createdAt) }}
        </el-descriptions-item>
        <el-descriptions-item label="最后在线时间">
          {{ formatDateTime(slave?.lastSeen) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <div class="slave-actions">
        <el-button
          type="warning"
          plain
          @click="handleViewMonitor"
        >
          查看监控
        </el-button>
        <el-button
          type="danger"
          plain
          :disabled="!slave?.isActive"
          @click="handleRestart"
        >
          重启服务器
        </el-button>
      </div>
    </el-card>
    
    <!-- 关联设备列表 -->
    <el-card class="devices-card">
      <template #header>
        <div class="card-header">
          <h3>关联设备</h3>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索设备名称"
              clearable
              style="width: 200px"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </template>
      
      <el-table
        v-loading="loading"
        :data="filteredDevices"
        style="width: 100%"
        @row-click="handleDeviceClick"
      >
        <el-table-column prop="name" label="设备名称" min-width="180">
          <template #default="{ row }">
            <div class="device-name">
              <el-icon :size="20" :class="getDeviceIcon(row.deviceType)" />
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="deviceType" label="设备类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getDeviceTypeName(row.deviceType) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="currentUser" label="当前使用者" width="120">
          <template #default="{ row }">
            <span v-if="row.currentUser">{{ row.currentUser }}</span>
            <el-tag v-else type="info" size="small">空闲</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              plain
              @click.stop="handleViewDeviceDetail(row)"
            >
              详情
            </el-button>
            <el-button
              type="warning"
              size="small"
              plain
              @click.stop="handleViewDeviceMonitor(row)"
            >
              监控
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 重启确认对话框 -->
    <el-dialog
      v-model="restartDialog.visible"
      title="重启服务器"
      width="400px"
    >
      <div class="restart-dialog-content">
        <p>确定要重启服务器 <strong>{{ slave?.name }}</strong> 吗？</p>
        <p class="restart-tips">重启过程中该服务器下的所有设备将暂时无法使用</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="restartDialog.visible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="restartDialog.loading"
            @click="confirmRestart"
          >
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Back, Monitor } from '@element-plus/icons-vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { formatDateTime } from '@/utils/format'
import { getSlaveById, restartSlave } from '@/api/slaves'
import { getDeviceList } from '@/api/devices'
import type { Slave } from '@/types/slave'
import type { Device, DeviceType } from '@/types/device'

const route = useRoute()
const router = useRouter()
const { subscribe, unsubscribe } = useWebSocket()

// 从服务器信息
const slave = ref<Slave | null>(null)
const loading = ref(false)

// 设备列表
const devices = ref<Device[]>([])
const searchKeyword = ref('')

// 重启对话框
const restartDialog = reactive({
  visible: false,
  loading: false
})

// 过滤后的设备列表
const filteredDevices = computed(() => {
  if (!searchKeyword.value) return devices.value
  const keyword = searchKeyword.value.toLowerCase()
  return devices.value.filter(device => 
    device.name.toLowerCase().includes(keyword)
  )
})

// 获取从服务器信息
const fetchSlaveInfo = async () => {
  try {
    loading.value = true
    const slaveId = Number(route.params.id)
    const data = await getSlaveById(slaveId)
    slave.value = data
  } catch (error) {
    console.error('Fetch slave info error:', error)
    ElMessage.error('获取从服务器信息失败')
  } finally {
    loading.value = false
  }
}

// 获取关联设备列表
const fetchDevices = async () => {
  try {
    loading.value = true
    const slaveId = Number(route.params.id)
    const { items } = await getDeviceList({
      page: 1,
      pageSize: 1000,
      slaveId
    })
    devices.value = items
  } catch (error) {
    console.error('Fetch devices error:', error)
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新
const handleRefresh = () => {
  fetchSlaveInfo()
  fetchDevices()
}

// 返回
const handleBack = () => {
  router.back()
}

// 查看监控
const handleViewMonitor = () => {
  if (!slave.value) return
  router.push(`/slaves/${slave.value.id}/monitor`)
}

// 重启服务器
const handleRestart = () => {
  restartDialog.visible = true
}

const confirmRestart = async () => {
  if (!slave.value) return
  
  try {
    restartDialog.loading = true
    await restartSlave(slave.value.id)
    ElMessage.success('重启命令已发送')
    fetchSlaveInfo()
  } catch (error) {
    console.error('Restart slave error:', error)
    ElMessage.error('重启失败')
  } finally {
    restartDialog.loading = false
    restartDialog.visible = false
  }
}

// 查看设备详情
const handleViewDeviceDetail = (device: Device) => {
  router.push(`/devices/${device.id}`)
}

// 查看设备监控
const handleViewDeviceMonitor = (device: Device) => {
  router.push(`/devices/${device.id}/monitor`)
}

// 点击设备行
const handleDeviceClick = (device: Device) => {
  handleViewDeviceDetail(device)
}

// 获取设备图标
const getDeviceIcon = (type: DeviceType) => {
  const icons: Record<DeviceType, string> = {
    usb: 'usb',
    serial: 'serial',
    parallel: 'parallel'
  }
  return icons[type] || 'device'
}

// 获取设备类型名称
const getDeviceTypeName = (type: DeviceType) => {
  const names: Record<DeviceType, string> = {
    usb: 'USB设备',
    serial: '串口设备',
    parallel: '并口设备'
  }
  return names[type] || type
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    online: 'success',
    offline: 'danger',
    occupied: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态名称
const getStatusName = (status: string) => {
  const names: Record<string, string> = {
    online: '在线',
    offline: '离线',
    occupied: '占用'
  }
  return names[status] || status
}

// WebSocket订阅从服务器和设备状态更新
const subscribeUpdates = () => {
  const slaveId = Number(route.params.id)
  
  // 订阅从服务器状态更新
  subscribe('slave_status', (data) => {
    const updatedSlave = data.slave
    if (updatedSlave.id === slaveId) {
      slave.value = { ...slave.value, ...updatedSlave }
    }
  })
  
  // 订阅设备状态更新
  subscribe('device_status', (data) => {
    const updatedDevice = data.device
    const index = devices.value.findIndex(d => d.id === updatedDevice.id)
    if (index !== -1) {
      devices.value[index] = { ...devices.value[index], ...updatedDevice }
    }
  })
}

onMounted(() => {
  fetchSlaveInfo()
  fetchDevices()
  subscribeUpdates()
})

onUnmounted(() => {
  unsubscribe('slave_status')
  unsubscribe('device_status')
})
</script>

<style scoped>
.slave-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.devices-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.slave-name,
.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.online {
  color: var(--el-color-success);
}

.offline {
  color: var(--el-color-danger);
}

.slave-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.restart-dialog-content {
  text-align: center;
}

.restart-tips {
  color: #909399;
  font-size: 14px;
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style> 