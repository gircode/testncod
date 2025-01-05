import request from '@/utils/request'

export interface Device {
  id: string
  name: string
  type: string
  serialNumber: string
  status: 'online' | 'offline' | 'error'
  currentUser?: string
  slaveName: string
  description?: string
  createdAt: string
  updatedAt: string
  lastActiveTime: string
}

export interface DeviceQuery {
  page?: number
  pageSize?: number
  type?: string
  status?: string
  search?: string
  slaveId?: string
}

export interface CreateDeviceParams {
  name: string
  type: string
  serialNumber: string
  slaveId: string
  description?: string
}

export interface UpdateDeviceParams extends Partial<CreateDeviceParams> {
  id: string
}

export function getDevices(params?: DeviceQuery) {
  return request<Device[]>({
    url: '/api/devices',
    method: 'get',
    params
  })
}

export function getDevice(id: string) {
  return request<Device>({
    url: `/api/devices/${id}`,
    method: 'get'
  })
}

export function createDevice(data: CreateDeviceParams) {
  return request<Device>({
    url: '/api/devices',
    method: 'post',
    data
  })
}

export function updateDevice(data: UpdateDeviceParams) {
  return request<Device>({
    url: `/api/devices/${data.id}`,
    method: 'put',
    data
  })
}

export function deleteDevice(id: string) {
  return request({
    url: `/api/devices/${id}`,
    method: 'delete'
  })
}

export function connectDevice(id: string) {
  return request<Device>({
    url: `/api/devices/${id}/connect`,
    method: 'post'
  })
}

export function disconnectDevice(id: string) {
  return request<Device>({
    url: `/api/devices/${id}/disconnect`,
    method: 'post'
  })
}

export function getDeviceStatus(id: string) {
  return request<{
    status: 'online' | 'offline' | 'error'
    lastActiveTime: string
    currentUser?: string
  }>({
    url: `/api/devices/${id}/status`,
    method: 'get'
  })
} 