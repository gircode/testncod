import request from '@/utils/request'

export interface Slave {
  id: string
  name: string
  ip: string
  port: number
  status: 'online' | 'offline' | 'error'
  version: string
  deviceCount: number
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkTraffic: number
  lastHeartbeat: string
  createdAt: string
  updatedAt: string
}

export interface SlaveQuery {
  page?: number
  pageSize?: number
  status?: string
  search?: string
}

export interface CreateSlaveParams {
  name: string
  ip: string
  port: number
  description?: string
}

export interface UpdateSlaveParams extends Partial<CreateSlaveParams> {
  id: string
}

export interface SlaveMetric {
  timestamp: string
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkTraffic: number
  deviceCount: number
  onlineDevices: number
  errorCount: number
}

export function getSlaves(params?: SlaveQuery) {
  return request<Slave[]>({
    url: '/api/slaves',
    method: 'get',
    params
  })
}

export function getSlaveById(id: string) {
  return request<Slave>({
    url: `/api/slaves/${id}`,
    method: 'get'
  })
}

export function createSlave(data: CreateSlaveParams) {
  return request<Slave>({
    url: '/api/slaves',
    method: 'post',
    data
  })
}

export function updateSlave(data: UpdateSlaveParams) {
  return request<Slave>({
    url: `/api/slaves/${data.id}`,
    method: 'put',
    data
  })
}

export function deleteSlave(id: string) {
  return request({
    url: `/api/slaves/${id}`,
    method: 'delete'
  })
}

export function getSlaveMetrics(id: string, timeRange: '1h' | '6h' | '24h') {
  return request<SlaveMetric[]>({
    url: `/api/slaves/${id}/metrics`,
    method: 'get',
    params: { timeRange }
  })
}

export function restartSlave(id: string) {
  return request({
    url: `/api/slaves/${id}/restart`,
    method: 'post'
  })
}

export function stopSlave(id: string) {
  return request({
    url: `/api/slaves/${id}/stop`,
    method: 'post'
  })
}

export function startSlave(id: string) {
  return request({
    url: `/api/slaves/${id}/start`,
    method: 'post'
  })
} 