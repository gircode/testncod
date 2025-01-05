<template>
  <div class="space-y-6">
    <!-- 状态概览 -->
    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">系统负载</dt>
                <dd class="flex items-baseline">
                  <div class="text-2xl font-semibold text-gray-900">{{ systemMetrics.load.toFixed(2) }}</div>
                  <div class="ml-2 flex items-baseline text-sm font-semibold" :class="systemMetrics.loadTrend > 0 ? 'text-red-600' : 'text-green-600'">
                    <svg v-if="systemMetrics.loadTrend > 0" class="self-center flex-shrink-0 h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                    <svg v-else class="self-center flex-shrink-0 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                    <span class="sr-only">{{ systemMetrics.loadTrend > 0 ? '增加' : '减少' }}</span>
                    {{ Math.abs(systemMetrics.loadTrend).toFixed(2) }}%
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">内存使用率</dt>
                <dd class="flex items-baseline">
                  <div class="text-2xl font-semibold text-gray-900">{{ systemMetrics.memory.toFixed(1) }}%</div>
                  <div class="ml-2 flex items-baseline text-sm font-semibold" :class="systemMetrics.memoryTrend > 0 ? 'text-red-600' : 'text-green-600'">
                    <svg v-if="systemMetrics.memoryTrend > 0" class="self-center flex-shrink-0 h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                    <svg v-else class="self-center flex-shrink-0 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                    <span class="sr-only">{{ systemMetrics.memoryTrend > 0 ? '增加' : '减少' }}</span>
                    {{ Math.abs(systemMetrics.memoryTrend).toFixed(1) }}%
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">设备在线率</dt>
                <dd class="flex items-baseline">
                  <div class="text-2xl font-semibold text-gray-900">{{ systemMetrics.deviceOnline.toFixed(1) }}%</div>
                  <div class="ml-2 flex items-baseline text-sm font-semibold" :class="systemMetrics.deviceOnlineTrend > 0 ? 'text-green-600' : 'text-red-600'">
                    <svg v-if="systemMetrics.deviceOnlineTrend > 0" class="self-center flex-shrink-0 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                    <svg v-else class="self-center flex-shrink-0 h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                    <span class="sr-only">{{ systemMetrics.deviceOnlineTrend > 0 ? '增加' : '减少' }}</span>
                    {{ Math.abs(systemMetrics.deviceOnlineTrend).toFixed(1) }}%
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">系统响应时间</dt>
                <dd class="flex items-baseline">
                  <div class="text-2xl font-semibold text-gray-900">{{ systemMetrics.responseTime }}ms</div>
                  <div class="ml-2 flex items-baseline text-sm font-semibold" :class="systemMetrics.responseTimeTrend > 0 ? 'text-red-600' : 'text-green-600'">
                    <svg v-if="systemMetrics.responseTimeTrend > 0" class="self-center flex-shrink-0 h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                    <svg v-else class="self-center flex-shrink-0 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                    <span class="sr-only">{{ systemMetrics.responseTimeTrend > 0 ? '增加' : '减少' }}</span>
                    {{ Math.abs(systemMetrics.responseTimeTrend).toFixed(0) }}ms
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 设备状态列表 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
        <h3 class="text-lg leading-6 font-medium text-gray-900">设备状态</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">设备名称</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CPU使用率</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">内存使用率</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最后心跳时间</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="device in devices" :key="device.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ device.name }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                  :class="{
                    'bg-green-100 text-green-800': device.status === 'online',
                    'bg-red-100 text-red-800': device.status === 'offline',
                    'bg-yellow-100 text-yellow-800': device.status === 'warning'
                  }"
                >
                  {{ device.status === 'online' ? '在线' : device.status === 'offline' ? '离线' : '警告' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ device.cpu }}%</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ device.memory }}%</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(device.lastHeartbeat) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { formatDate } from '@/utils/format'

interface SystemMetrics {
  load: number
  loadTrend: number
  memory: number
  memoryTrend: number
  deviceOnline: number
  deviceOnlineTrend: number
  responseTime: number
  responseTimeTrend: number
}

interface Device {
  id: number
  name: string
  status: 'online' | 'offline' | 'warning'
  cpu: number
  memory: number
  lastHeartbeat: string
}

// 模拟数据
const systemMetrics = ref<SystemMetrics>({
  load: 1.5,
  loadTrend: -0.2,
  memory: 65.8,
  memoryTrend: 2.3,
  deviceOnline: 92.5,
  deviceOnlineTrend: 1.2,
  responseTime: 120,
  responseTimeTrend: -15
})

const devices = ref<Device[]>([
  {
    id: 1,
    name: '设备-001',
    status: 'online',
    cpu: 35,
    memory: 45,
    lastHeartbeat: new Date().toISOString()
  },
  {
    id: 2,
    name: '设备-002',
    status: 'warning',
    cpu: 85,
    memory: 78,
    lastHeartbeat: new Date().toISOString()
  },
  {
    id: 3,
    name: '设备-003',
    status: 'offline',
    cpu: 0,
    memory: 0,
    lastHeartbeat: new Date(Date.now() - 3600000).toISOString()
  }
])

let timer: number

// 模拟实时更新数据
const updateMetrics = () => {
  systemMetrics.value = {
    load: 1.5 + Math.random() * 0.5 - 0.25,
    loadTrend: Math.random() * 0.4 - 0.2,
    memory: 65.8 + Math.random() * 4 - 2,
    memoryTrend: Math.random() * 4 - 2,
    deviceOnline: 92.5 + Math.random() * 2 - 1,
    deviceOnlineTrend: Math.random() * 2 - 1,
    responseTime: 120 + Math.round(Math.random() * 40 - 20),
    responseTimeTrend: Math.round(Math.random() * 30 - 15)
  }

  devices.value = devices.value.map(device => ({
    ...device,
    cpu: device.status === 'online' ? Math.round(Math.random() * 40 + 30) : device.cpu,
    memory: device.status === 'online' ? Math.round(Math.random() * 30 + 40) : device.memory,
    lastHeartbeat: device.status === 'online' ? new Date().toISOString() : device.lastHeartbeat
  }))
}

onMounted(() => {
  // 每5秒更新一次数据
  timer = window.setInterval(updateMetrics, 5000)
})

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script> 