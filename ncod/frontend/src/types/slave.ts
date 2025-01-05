// 从服务器状态类型
export type SlaveStatus = 'online' | 'offline'

// 从服务器接口
export interface Slave {
  id: string
  name: string
  ip: string
  port: number
  status: SlaveStatus
  cpuUsage: number
  memoryUsage: number
  lastHeartbeat: string
  description?: string
  deviceCount?: number
  activeConnections?: number
  errorCount?: number
  responseTime?: number
  uptime?: number
  usbBandwidth?: number
  deviceErrors?: Array<{
    deviceId: string
    error: string
    timestamp: string
  }>
}

// 从服务器列表查询参数
export interface SlaveListQuery {
  page: number
  pageSize: number
  keyword?: string
  status?: SlaveStatus
}

// 从服务器表单数据
export interface SlaveForm {
  name: string
  ip: string
  port: number
  description?: string
}

// 从服务器性能指标
export interface SlaveMetrics {
  cpuUsage: number
  memoryUsage: number
  deviceCount: number
  activeConnections: number
  errorCount: number
  responseTime: number
  uptime: number
  usbBandwidth: number
  deviceErrors: Array<{
    deviceId: string
    error: string
    timestamp: string
  }>
}

// 从服务器监控数据
export interface SlaveMonitorData {
  metrics: SlaveMetrics
  timestamp: string
}

// 从服务器设置
export interface SlaveSettings {
  name: string
  description?: string
  maxDevices?: number
  maxConnections?: number
  usbSettings: {
    enableHubFiltering: boolean
    allowedHubs: string[]
    blockedHubs: string[]
  }
  deviceRules: DeviceRule[]
}

// 设备规则
export interface DeviceRule {
  id: string
  type: 'whitelist' | 'blacklist'
  vendorId?: string
  productId?: string
  serialNumber?: string
  description?: string
} 