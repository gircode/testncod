import request from '@/utils/request'

export function getSystemMetrics() {
  return request({
    url: '/api/monitor/metrics',
    method: 'get'
  })
}

export function getDevices() {
  return request({
    url: '/api/monitor/devices',
    method: 'get'
  })
}

export function getDeviceDetail(deviceId) {
  return request({
    url: `/api/monitor/devices/${deviceId}`,
    method: 'get'
  })
}

export function getPortStatus(deviceId) {
  return request({
    url: `/api/monitor/devices/${deviceId}/ports`,
    method: 'get'
  })
} 