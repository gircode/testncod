<template>
  <el-dialog title="导出进度" v-model="visible" width="400px" :close-on-click-modal="false" :close-on-press-escape="false"
    :show-close="status === 'failed'">
    <div class="export-progress">
      <el-progress :percentage="progress" :status="status === 'failed' ? 'exception' : undefined" />

      <div class="status-message" v-if="status === 'pending'">
        正在准备导出...
      </div>
      <div class="status-message" v-else-if="status === 'processing'">
        正在导出数据...
      </div>
      <div class="status-message" v-else-if="status === 'completed'">
        导出完成！
      </div>
      <div class="status-message error" v-else-if="status === 'failed'">
        {{ error || '导出失败' }}
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { ExportProgressProps } from '@/types/props'
import type { ExportTask } from '@/types/api'
import { getExportStatus } from '@/api/device'
import { logger } from '@/utils/logger'

const props = defineProps<ExportProgressProps>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'completed': [fileUrl: string]
}>()

const progress = ref(0)
const status = ref<ExportTask['status']>('pending')
const error = ref<string>()
const fileUrl = ref<string>()
const checkInterval = ref<number>()

const startPolling = (taskId: string) => {
  checkInterval.value = window.setInterval(async () => {
    try {
      const response = await getExportStatus(taskId)
      progress.value = response.progress
      status.value = response.status
      error.value = response.error
      fileUrl.value = response.file_url

      if (['completed', 'failed'].includes(response.status)) {
        stopPolling()
        if (response.status === 'completed' && response.file_url) {
          emit('completed', response.file_url)
          setTimeout(() => {
            emit('update:visible', false)
          }, 1000)
        }
      }
    } catch (err) {
      logger.error('Failed to check export status:', err)
      stopPolling()
      error.value = '检查导出状态失败'
    }
  }, 2000)
}

const stopPolling = () => {
  if (checkInterval.value) {
    clearInterval(checkInterval.value)
    checkInterval.value = undefined
  }
}

watch(() => props.taskId, (newTaskId) => {
  stopPolling()
  if (newTaskId) {
    progress.value = 0
    status.value = 'pending'
    error.value = undefined
    fileUrl.value = undefined
    startPolling(newTaskId)
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.export-progress {
  padding: 20px 0;
}

.status-message {
  margin-top: 20px;
  text-align: center;
  color: #666;
}

.status-message.error {
  color: #f56c6c;
}
</style>