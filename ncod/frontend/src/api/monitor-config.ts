import request from '@/utils/request'

export interface MonitorConfig {
  id: string
  name: string
  description: string
  target: string
  metrics: string[]
  interval: number
  retention: number
  enabled: boolean
  createdAt: string
  updatedAt: string
}

export interface CreateMonitorConfigParams {
  name: string
  description?: string
  target: string
  metrics: string[]
  interval: number
  retention: number
  enabled?: boolean
}

export interface UpdateMonitorConfigParams extends Partial<CreateMonitorConfigParams> {
  id: string
}

export function getMonitorConfigs() {
  return request<MonitorConfig[]>({
    url: '/api/monitor-configs',
    method: 'get'
  })
}

export function getMonitorConfig(id: string) {
  return request<MonitorConfig>({
    url: `/api/monitor-configs/${id}`,
    method: 'get'
  })
}

export function createMonitorConfig(data: CreateMonitorConfigParams) {
  return request<MonitorConfig>({
    url: '/api/monitor-configs',
    method: 'post',
    data
  })
}

export function updateMonitorConfig(data: UpdateMonitorConfigParams) {
  return request<MonitorConfig>({
    url: `/api/monitor-configs/${data.id}`,
    method: 'put',
    data
  })
}

export function deleteMonitorConfig(id: string) {
  return request({
    url: `/api/monitor-configs/${id}`,
    method: 'delete'
  })
}

export function enableMonitorConfig(id: string) {
  return request({
    url: `/api/monitor-configs/${id}/enable`,
    method: 'post'
  })
}

export function disableMonitorConfig(id: string) {
  return request({
    url: `/api/monitor-configs/${id}/disable`,
    method: 'post'
  })
} 