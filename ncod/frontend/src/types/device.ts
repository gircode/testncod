// 设备状态类型
export type DeviceStatus = 'online' | 'offline' | 'using' | 'error'

// 设备类型接口
export interface Device {
  id: string
  name: string
  type: string
  status: 'online' | 'offline'
  vendorId: string
  productId: string
  serialNumber: string
  description?: string
  lastSeen?: string
  connected?: boolean
  inUse?: boolean
  userId?: string
  slaveId?: string
}

// 设备列表查询参数
export interface DeviceListQuery {
  page: number
  pageSize: number
  keyword?: string
  status?: DeviceStatus
  slaveId?: string
  type?: string
}

// 设备列表响应
export interface DeviceListResponse {
  code: number
  message: string
  data: {
    total: number
    items: Device[]
  }
}

// 设备使用记录
export interface DeviceUsageRecord {
  id: string
  deviceId: string
  deviceName: string
  userId: string
  username: string
  startTime: string
  endTime?: string
  duration?: number
  status: 'active' | 'completed' | 'interrupted'
}

// 设备统计数据
export interface DeviceStats {
  deviceId: string
  timestamp: string
  cpuUsage: number
  memoryUsage: number
  networkIn: number
  networkOut: number
  errorCount: number
}

export interface DeviceFilter {
  type?: string[]
  status?: ('online' | 'offline')[]
  search?: string
  slaveId?: string
  userId?: string
} 