import request from '@/utils/request'

export interface MonitoringMetrics {
  timestamp: string
  cpu: {
    usage: number
    temperature: number
    cores: number[]
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
    io: {
      read: number
      write: number
    }
  }
  network: {
    in: number
    out: number
    connections: number
  }
  system: {
    uptime: number
    processes: number
    threads: number
    load: number[]
  }
}

export interface MonitoringQuery {
  startTime?: string
  endTime?: string
  interval?: number
  type?: 'cpu' | 'memory' | 'disk' | 'network' | 'system'
}

export interface MonitoringAlert {
  id: string
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'system'
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  timestamp: string
  resolved: boolean
  resolvedAt?: string
}

export interface MonitoringRule {
  id: string
  name: string
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'system'
  condition: 'gt' | 'lt' | 'eq' | 'ne'
  threshold: number
  duration: number
  level: 'info' | 'warning' | 'error' | 'critical'
  enabled: boolean
}

export function getMonitoringMetrics(params?: MonitoringQuery) {
  return request<MonitoringMetrics[]>({
    url: '/api/monitoring/metrics',
    method: 'get',
    params
  })
}

export function getLatestMetrics() {
  return request<MonitoringMetrics>({
    url: '/api/monitoring/metrics/latest',
    method: 'get'
  })
}

export function getMonitoringAlerts(params?: {
  startTime?: string
  endTime?: string
  type?: string
  level?: string
  resolved?: boolean
}) {
  return request<MonitoringAlert[]>({
    url: '/api/monitoring/alerts',
    method: 'get',
    params
  })
}

export function resolveAlert(id: string) {
  return request<MonitoringAlert>({
    url: `/api/monitoring/alerts/${id}/resolve`,
    method: 'post'
  })
}

export function getMonitoringRules() {
  return request<MonitoringRule[]>({
    url: '/api/monitoring/rules',
    method: 'get'
  })
}

export function createMonitoringRule(data: Omit<MonitoringRule, 'id'>) {
  return request<MonitoringRule>({
    url: '/api/monitoring/rules',
    method: 'post',
    data
  })
}

export function updateMonitoringRule(id: string, data: Partial<Omit<MonitoringRule, 'id'>>) {
  return request<MonitoringRule>({
    url: `/api/monitoring/rules/${id}`,
    method: 'put',
    data
  })
}

export function deleteMonitoringRule(id: string) {
  return request({
    url: `/api/monitoring/rules/${id}`,
    method: 'delete'
  })
}

export function enableMonitoringRule(id: string) {
  return request<MonitoringRule>({
    url: `/api/monitoring/rules/${id}/enable`,
    method: 'post'
  })
}

export function disableMonitoringRule(id: string) {
  return request<MonitoringRule>({
    url: `/api/monitoring/rules/${id}/disable`,
    method: 'post'
  })
} 