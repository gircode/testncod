<template>
  <div class="device-connector">
    <el-dialog
      :title="`连接设备: ${device?.name}`"
      v-model="visible"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="connection-status">
        <el-steps :active="currentStep" finish-status="success">
          <el-step title="初始化连接" />
          <el-step title="设备分配" />
          <el-step title="建立连接" />
        </el-steps>
        
        <div class="status-message" v-if="statusMessage">
          {{ statusMessage }}
          <span v-if="retryCount > 0">
            (重试次数: {{ retryCount }}/{{ maxRetries }})
          </span>
        </div>
        
        <div class="connection-progress" v-if="connecting">
          <el-progress :percentage="progress" />
        </div>
      </div>
      
      <template #footer>
        <el-button @click="handleCancel" :disabled="connecting">
          取消
        </el-button>
        <el-button 
          type="primary" 
          @click="handleConnect" 
          :loading="connecting"
          :disabled="connecting"
        >
          连接
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { DeviceInfo } from '@/types'
import { connectDevice } from '@/api/device'
import { DeviceError, DeviceErrorCodes } from '@/types/errors'
import type { DeviceConnectorProps } from '@/types/props'
import { logger } from '@/utils/logger'

const props = defineProps<DeviceConnectorProps>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'connected': []
  'failed': [error: DeviceError]
}>()

const currentStep = ref(1)
const statusMessage = ref('')
const retryCount = ref(0)
const maxRetries = 3
const retryDelay = 2000 // 2秒后重试
const connecting = ref(false)
const progress = ref(0)

const resetState = () => {
  currentStep.value = 1
  statusMessage.value = ''
  retryCount.value = 0
  connecting.value = false
  progress.value = 0
}

const shouldRetry = (error: any) => {
  if (error instanceof DeviceError) {
    return [
      DeviceErrorCodes.CONNECTION_FAILED,
      DeviceErrorCodes.TIMEOUT,
      DeviceErrorCodes.NETWORK_ERROR
    ].includes(error.code)
  }
  return true
}

const getErrorMessage = (error: any) => {
  if (error instanceof DeviceError) {
    return error.message
  }
  return '连接失败，请重试'
}

const connectWithRetry = async () => {
  while (true) {
    try {
      statusMessage.value = '正在初始化连接...'
      currentStep.value = 1
      progress.value = 30
      
      await connectDevice(props.device.id)
      
      statusMessage.value = '连接成功'
      currentStep.value = 3
      progress.value = 100
      emit('connected')
      
      setTimeout(() => {
        emit('update:visible', false)
      }, 1000)
      return
      
    } catch (error) {
      logger.error('Device connection failed', error)
      
      if (!shouldRetry(error) || retryCount.value >= maxRetries) {
        throw error
      }
      
      retryCount.value++
      const errorMessage = getErrorMessage(error)
      statusMessage.value = `${errorMessage}，${retryDelay/1000}秒后重试...`
      await new Promise(resolve => setTimeout(resolve, retryDelay))
    }
  }
}

const handleConnect = async () => {
  try {
    connecting.value = true
    await connectWithRetry()
  } catch (error) {
    const errorMessage = getErrorMessage(error)
    ElMessage.error(errorMessage)
    emit('failed', error)
  } finally {
    connecting.value = false
  }
}

const handleCancel = () => {
  if (!connecting.value) {
    resetState()
    emit('update:visible', false)
  }
}

onUnmounted(() => {
  resetState()
})
</script>

<style scoped>
.device-connector {
  .connection-status {
    padding: 20px 0;
  }
  
  .status-message {
    margin-top: 20px;
    text-align: center;
    color: #666;
  }
  
  .connection-progress {
    margin-top: 20px;
  }
}
</style> 