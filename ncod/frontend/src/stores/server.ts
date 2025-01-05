import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ServerMetrics {
  cpu: {
    usage: number
    temperature: number
    cores: number
  }
  memory: {
    total: number
    used: number
    free: number
    usage: number
  }
  disk: {
    total: number
    used: number
    free: number
    usage: number
  }
  network: {
    bandwidth: {
      in: number
      out: number
    }
    connections: number
  }
  system: {
    uptime: number
    processes: number
    threads: number
    load: number[]
  }
}

export interface ServerStatus {
  status: 'online' | 'offline' | 'error'
  lastUpdate: string
  version: string
  hostname: string
  os: string
}

export const useServerStore = defineStore('server', () => {
  const currentMetrics = ref<ServerMetrics | null>(null)
  const serverStatus = ref<ServerStatus | null>(null)
  const metricsHistory = ref<ServerMetrics[]>([])

  const isOnline = computed(() => serverStatus.value?.status === 'online')
  const cpuUsage = computed(() => currentMetrics.value?.cpu.usage || 0)
  const memoryUsage = computed(() => currentMetrics.value?.memory.usage || 0)
  const diskUsage = computed(() => currentMetrics.value?.disk.usage || 0)

  function setMetrics(metrics: ServerMetrics) {
    currentMetrics.value = metrics
    metricsHistory.value.push(metrics)
    if (metricsHistory.value.length > 100) {
      metricsHistory.value.shift()
    }
  }

  function setStatus(status: ServerStatus) {
    serverStatus.value = status
  }

  function clearMetrics() {
    currentMetrics.value = null
    serverStatus.value = null
    metricsHistory.value = []
  }

  return {
    currentMetrics,
    serverStatus,
    metricsHistory,
    isOnline,
    cpuUsage,
    memoryUsage,
    diskUsage,
    setMetrics,
    setStatus,
    clearMetrics
  }
}) 