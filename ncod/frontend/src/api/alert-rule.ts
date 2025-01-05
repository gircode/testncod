import request from '@/utils/request'

export interface AlertRule {
  id: string
  name: string
  description: string
  target: string
  metric: string
  condition: 'gt' | 'lt' | 'eq' | 'ne' | 'ge' | 'le'
  threshold: number
  duration: number
  severity: 'info' | 'warning' | 'error' | 'critical'
  enabled: boolean
  createdAt: string
  updatedAt: string
}

export interface CreateAlertRuleParams {
  name: string
  description?: string
  target: string
  metric: string
  condition: 'gt' | 'lt' | 'eq' | 'ne' | 'ge' | 'le'
  threshold: number
  duration: number
  severity: 'info' | 'warning' | 'error' | 'critical'
  enabled?: boolean
}

export interface UpdateAlertRuleParams extends Partial<CreateAlertRuleParams> {
  id: string
}

export function getAlertRules() {
  return request<AlertRule[]>({
    url: '/api/alert-rules',
    method: 'get'
  })
}

export function getAlertRule(id: string) {
  return request<AlertRule>({
    url: `/api/alert-rules/${id}`,
    method: 'get'
  })
}

export function createAlertRule(data: CreateAlertRuleParams) {
  return request<AlertRule>({
    url: '/api/alert-rules',
    method: 'post',
    data
  })
}

export function updateAlertRule(data: UpdateAlertRuleParams) {
  return request<AlertRule>({
    url: `/api/alert-rules/${data.id}`,
    method: 'put',
    data
  })
}

export function deleteAlertRule(id: string) {
  return request({
    url: `/api/alert-rules/${id}`,
    method: 'delete'
  })
}

export function enableAlertRule(id: string) {
  return request({
    url: `/api/alert-rules/${id}/enable`,
    method: 'post'
  })
}

export function disableAlertRule(id: string) {
  return request({
    url: `/api/alert-rules/${id}/disable`,
    method: 'post'
  })
} 