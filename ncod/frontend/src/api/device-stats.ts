import request from '@/utils/request'

export interface DeviceStats {
  deviceId: string
  timestamp: string
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkIn: number
  networkOut: number
  errorCount: number
  status: 'online' | 'offline' | 'error'
  lastActiveTime: string
  metadata?: Record<string, any>
}

export interface DeviceStatsQuery {
  startTime?: string
  endTime?: string
  interval?: number
  type?: 'cpu' | 'memory' | 'disk' | 'network'
  deviceIds?: string[]
}

export interface DeviceStatsAggregation {
  deviceId: string
  period: string
  data: {
    cpuUsage: {
      min: number
      max: number
      avg: number
    }
    memoryUsage: {
      min: number
      max: number
      avg: number
    }
    diskUsage: {
      min: number
      max: number
      avg: number
    }
    networkTraffic: {
      in: {
        min: number
        max: number
        avg: number
      }
      out: {
        min: number
        max: number
        avg: number
      }
    }
  }
}

export function getDeviceStats(deviceId: string, params?: DeviceStatsQuery) {
  return request<DeviceStats[]>({
    url: `/api/device-stats/${deviceId}`,
    method: 'get',
    params
  })
}

export function getDeviceStatsAggregation(deviceId: string, period: 'hour' | 'day' | 'week' | 'month') {
  return request<DeviceStatsAggregation>({
    url: `/api/device-stats/${deviceId}/aggregation`,
    method: 'get',
    params: { period }
  })
}

export function getMultiDeviceStats(params: DeviceStatsQuery & { deviceIds: string[] }) {
  return request<Record<string, DeviceStats[]>>({
    url: '/api/device-stats/multi',
    method: 'get',
    params
  })
}

export function getLatestDeviceStats(deviceId: string) {
  return request<DeviceStats>({
    url: `/api/device-stats/${deviceId}/latest`,
    method: 'get'
  })
}

export function exportDeviceStats(deviceId: string, params: DeviceStatsQuery) {
  return request({
    url: `/api/device-stats/${deviceId}/export`,
    method: 'get',
    params,
    responseType: 'blob'
  })
}

export function clearDeviceStats(deviceId: string, params?: { 
  before?: string
  type?: 'cpu' | 'memory' | 'disk' | 'network' 
}) {
  return request({
    url: `/api/device-stats/${deviceId}/clear`,
    method: 'post',
    data: params
  })
} 