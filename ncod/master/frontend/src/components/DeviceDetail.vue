<template>
  <div class="device-detail">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="设备名称">{{ device.name }}</el-descriptions-item>
      <el-descriptions-item label="IP地址">{{ device.ip_address }}</el-descriptions-item>
      <el-descriptions-item label="MAC地址">{{ device.mac_address }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getStatusType(device.status)">
          {{ getStatusText(device.status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="最后在线时间">
        {{ formatDateTime(device.last_online) }}
      </el-descriptions-item>
      <el-descriptions-item label="所属组">{{ device.group?.name }}</el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup>
import { formatDateTime } from '@/utils/format'

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

const getStatusType = (status) => {
  const types = {
    online: 'success',
    offline: 'info',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    online: '在线',
    offline: '离线',
    error: '异常'
  }
  return texts[status] || status
}
</script> 