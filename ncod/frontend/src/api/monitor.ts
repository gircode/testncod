import request from '@/utils/request'

export interface MonitorData {
  timestamp: string
  type: 'cpu' | 'memory' | 'disk' | 'network'
  value: number
  metadata?: Record<string, any>
}

export interface MonitorQuery {
  startTime?: string
  endTime?: string
  type?: 'cpu' | 'memory' | 'disk' | 'network'
  interval?: number
  limit?: number
}

export interface MonitorStats {
  min: number
  max: number
  avg: number
  current: number
  trend: 'up' | 'down' | 'stable'
}

export interface MonitorSummary {
  cpu: MonitorStats
  memory: MonitorStats
  disk: MonitorStats
  network: MonitorStats
  lastUpdate: string
}

export function getMonitorData(params: MonitorQuery) {
  return request<MonitorData[]>({
    url: '/api/monitor/data',
    method: 'get',
    params
  })
}

export function getMonitorStats(type: 'cpu' | 'memory' | 'disk' | 'network') {
  return request<MonitorStats>({
    url: `/api/monitor/stats/${type}`,
    method: 'get'
  })
}

export function getMonitorSummary() {
  return request<MonitorSummary>({
    url: '/api/monitor/summary',
    method: 'get'
  })
}

export function exportMonitorData(params: MonitorQuery) {
  return request({
    url: '/api/monitor/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

export function clearMonitorData(type?: 'cpu' | 'memory' | 'disk' | 'network') {
  return request({
    url: '/api/monitor/clear',
    method: 'post',
    data: { type }
  })
} 