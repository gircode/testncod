<template>
  <div class="settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>

      <el-form :model="settingsForm" label-width="120px">
        <!-- 系统设置 -->
        <el-divider>系统配置</el-divider>
        <el-form-item label="系统名称">
          <el-input v-model="settingsForm.systemName" />
        </el-form-item>
        
        <!-- 从机设置 -->
        <el-divider>从机配置</el-divider>
        <el-form-item label="心跳检测间隔">
          <el-input-number 
            v-model="settingsForm.heartbeatInterval" 
            :min="1" 
            :max="60"
          /> 秒
        </el-form-item>
        
        <!-- 设备设置 -->
        <el-divider>设备配置</el-divider>
        <el-form-item label="自动重连">
          <el-switch v-model="settingsForm.autoReconnect" />
        </el-form-item>
        
        <!-- 日志设置 -->
        <el-divider>日志配置</el-divider>
        <el-form-item label="日志级别">
          <el-select v-model="settingsForm.logLevel">
            <el-option label="DEBUG" value="debug" />
            <el-option label="INFO" value="info" />
            <el-option label="WARNING" value="warning" />
            <el-option label="ERROR" value="error" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave">保存设置</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const settingsForm = ref({
  systemName: 'NCOD 设备管理系统',
  heartbeatInterval: 30,
  autoReconnect: true,
  logLevel: 'info'
})

const handleSave = async () => {
  try {
    // 这里添加保存设置的逻辑
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('设置保存失败')
  }
}

const handleReset = () => {
  settingsForm.value = {
    systemName: 'NCOD 设备管理系统',
    heartbeatInterval: 30,
    autoReconnect: true,
    logLevel: 'info'
  }
}
</script>

<style scoped>
.settings {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 