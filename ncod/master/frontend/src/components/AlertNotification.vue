<template>
  <div class="alert-notification">
    <el-alert
      v-for="alert in alerts"
      :key="alert.id"
      :title="getAlertTitle(alert)"
      :type="getAlertType(alert)"
      :description="getAlertDescription(alert)"
      show-icon
      :closable="true"
      @close="handleClose(alert)"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { formatDateTime } from '@/utils/format'

const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close'])

const getAlertTitle = (alert) => {
  const titles = {
    system_alert: '系统告警',
    device_alert: '设备告警',
    security_alert: '安全告警'
  }
  return titles[alert.type] || '未知告警'
}

const getAlertType = (alert) => {
  if (alert.severity === 'critical') return 'error'
  if (alert.severity === 'warning') return 'warning'
  return 'info'
}

const getAlertDescription = (alert) => {
  let description = `${alert.message}`
  if (alert.timestamp) {
    description += ` (${formatDateTime(alert.timestamp)})`
  }
  return description
}

const handleClose = (alert) => {
  emit('close', alert)
}
</script>

<style scoped>
.alert-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  width: 400px;
}

.el-alert {
  margin-bottom: 10px;
}
</style> 