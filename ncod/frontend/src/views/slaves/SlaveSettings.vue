<template>
  <div class="slave-settings">
    <a-card class="mb-4">
      <template #title>从服务器设置</template>
      <template #extra>
        <a-button type="primary" @click="saveSettings">
          保存设置
        </a-button>
      </template>

      <!-- 基本设置 -->
      <a-form :model="settings" layout="vertical">
        <a-form-item label="服务器名称" required>
          <a-input v-model="settings.name" placeholder="请输入服务器名称" />
        </a-form-item>
        
        <a-form-item label="描述">
          <a-textarea v-model="settings.description" placeholder="请输入服务器描述" />
        </a-form-item>

        <a-divider>VirtualHere 设置</a-divider>
        
        <a-form-item label="VirtualHere 服务端口" required>
          <a-input-number v-model="settings.virtualHere.port" :min="1" :max="65535" />
        </a-form-item>
        
        <a-form-item label="SSL 加密">
          <a-switch v-model="settings.virtualHere.ssl.enabled" />
        </a-form-item>
        
        <a-form-item v-if="settings.virtualHere.ssl.enabled" label="SSL 证书路径">
          <a-input v-model="settings.virtualHere.ssl.certPath" placeholder="请输入SSL证书路径" />
        </a-form-item>
        
        <a-form-item label="自动启动">
          <a-switch v-model="settings.virtualHere.autoStart" />
        </a-form-item>

        <a-divider>设备授权</a-divider>
        
        <a-form-item label="设备授权脚本">
          <a-textarea 
            v-model="settings.virtualHere.authScript" 
            :rows="6"
            placeholder="#!/bin/bash&#10;# 设备授权脚本"
          />
        </a-form-item>
        
        <a-form-item label="启用MAC地址验证">
          <a-switch v-model="settings.virtualHere.macAuth" />
        </a-form-item>

        <a-divider>性能设置</a-divider>
        
        <a-form-item label="最大设备连接数">
          <a-input-number v-model="settings.performance.maxDevices" :min="1" :max="122" />
        </a-form-item>
        
        <a-form-item label="设备扫描间隔(秒)">
          <a-input-number v-model="settings.performance.scanInterval" :min="1" :max="3600" />
        </a-form-item>
        
        <a-form-item label="性能数据上报间隔(秒)">
          <a-input-number v-model="settings.performance.reportInterval" :min="1" :max="3600" />
        </a-form-item>

        <a-divider>告警设置</a-divider>
        
        <a-form-item label="CPU使用率告警阈值(%)">
          <a-input-number v-model="settings.alerts.cpuThreshold" :min="0" :max="100" />
        </a-form-item>
        
        <a-form-item label="内存使用率告警阈值(%)">
          <a-input-number v-model="settings.alerts.memoryThreshold" :min="0" :max="100" />
        </a-form-item>
        
        <a-form-item label="磁盘使用率告警阈值(%)">
          <a-input-number v-model="settings.alerts.diskThreshold" :min="0" :max="100" />
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 设备黑白名单 -->
    <a-card class="mb-4">
      <template #title>设备访问控制</template>
      
      <a-tabs>
        <a-tab-pane key="whitelist" tab="白名单">
          <a-button type="primary" class="mb-4" @click="addWhitelistDevice">
            添加设备
          </a-button>
          
          <a-table :columns="deviceColumns" :data-source="settings.whitelist">
            <template #action="{ record }">
              <a-button type="link" danger @click="removeDevice('whitelist', record)">
                删除
              </a-button>
            </template>
          </a-table>
        </a-tab-pane>
        
        <a-tab-pane key="blacklist" tab="黑名单">
          <a-button type="primary" class="mb-4" @click="addBlacklistDevice">
            添加设备
          </a-button>
          
          <a-table :columns="deviceColumns" :data-source="settings.blacklist">
            <template #action="{ record }">
              <a-button type="link" danger @click="removeDevice('blacklist', record)">
                删除
              </a-button>
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>

  <!-- 添加设备弹窗 -->
  <a-modal
    v-model:visible="deviceModal.visible"
    :title="deviceModal.title"
    @ok="handleDeviceModalOk"
  >
    <a-form :model="deviceModal.form" layout="vertical">
      <a-form-item label="设备名称" required>
        <a-input v-model="deviceModal.form.name" />
      </a-form-item>
      
      <a-form-item label="Vendor ID" required>
        <a-input v-model="deviceModal.form.vendorId" />
      </a-form-item>
      
      <a-form-item label="Product ID" required>
        <a-input v-model="deviceModal.form.productId" />
      </a-form-item>
      
      <a-form-item label="序列号">
        <a-input v-model="deviceModal.form.serialNumber" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { SlaveSettings, DeviceRule } from '@/types/slave'

// 设置数据
const settings = ref<SlaveSettings>({
  name: '',
  description: '',
  virtualHere: {
    port: 7575,
    ssl: {
      enabled: false,
      certPath: ''
    },
    autoStart: true,
    authScript: '',
    macAuth: false
  },
  performance: {
    maxDevices: 50,
    scanInterval: 30,
    reportInterval: 60
  },
  alerts: {
    cpuThreshold: 80,
    memoryThreshold: 80,
    diskThreshold: 90
  },
  whitelist: [],
  blacklist: []
})

// 设备列表列定义
const deviceColumns = [
  { title: '设备名称', dataIndex: 'name' },
  { title: 'Vendor ID', dataIndex: 'vendorId' },
  { title: 'Product ID', dataIndex: 'productId' },
  { title: '序列号', dataIndex: 'serialNumber' },
  { title: '操作', slots: { customRender: 'action' } }
]

// 设备弹窗状态
const deviceModal = ref({
  visible: false,
  title: '',
  type: '' as 'whitelist' | 'blacklist',
  form: {
    name: '',
    vendorId: '',
    productId: '',
    serialNumber: ''
  }
})

// 加载设置
onMounted(async () => {
  try {
    const response = await fetch('/api/slave/settings')
    const data = await response.json()
    settings.value = data
  } catch (error) {
    message.error('加载设置失败')
    console.error(error)
  }
})

// 保存设置
const saveSettings = async () => {
  try {
    await fetch('/api/slave/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings.value)
    })
    message.success('保存成功')
  } catch (error) {
    message.error('保存失败')
    console.error(error)
  }
}

// 添加白名单设备
const addWhitelistDevice = () => {
  deviceModal.value = {
    visible: true,
    title: '添加白名单设备',
    type: 'whitelist',
    form: {
      name: '',
      vendorId: '',
      productId: '',
      serialNumber: ''
    }
  }
}

// 添加黑名单设备
const addBlacklistDevice = () => {
  deviceModal.value = {
    visible: true,
    title: '添加黑名单设备',
    type: 'blacklist',
    form: {
      name: '',
      vendorId: '',
      productId: '',
      serialNumber: ''
    }
  }
}

// 处理设备弹窗确认
const handleDeviceModalOk = () => {
  const { type, form } = deviceModal.value
  settings.value[type].push({
    ...form,
    id: Date.now().toString()
  })
  deviceModal.value.visible = false
}

// 移除设备
const removeDevice = (type: 'whitelist' | 'blacklist', device: DeviceRule) => {
  settings.value[type] = settings.value[type].filter((d: DeviceRule) => d.id !== device.id)
}
</script>

<style scoped>
.slave-settings {
  padding: 24px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style> 