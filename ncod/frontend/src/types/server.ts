export type ServerStatus = 'online' | 'offline' | 'warning' | 'error'

export interface MasterServer extends Server {
    slaveCount: number
    totalDevices: number
    activeDevices: number
    lastBackup: string
    version: string
}

export interface SlaveServer extends Server {
    masterId: string
    maxDevices: number
    currentDevices: number
    lastHeartbeat: string
    region: string
}

export interface ServerPerformance {
    timestamp: string
    metrics: ServerMetrics
}

export interface NetworkInterface {
  name: string
  bytesIn: number
  bytesOut: number
  packetsIn: number
  packetsOut: number
  errors: {
    in: number
    out: number
  }
  drops: {
    in: number
    out: number
  }
}

export interface ServerMetrics {
  cpu: {
    usage: number
    cores: number
    temperature?: number
  }
  memory: {
    total: number
    used: number
    free: number
  }
  disk: {
    total: number
    used: number
    free: number
  }
  network: {
    interfaces: {
      name: string
      bytesIn: number
      bytesOut: number
      packetsIn: number
      packetsOut: number
    }[]
  }
}

export interface Server {
  id: string
  name: string
  ip: string
  port: number
  status: ServerStatus
  description: string
  metrics: ServerMetrics
  lastUpdated: string
}

export interface BatchOperation {
  type: 'restart' | 'shutdown' | 'update'
  target_ids: string[]
  params?: Record<string, any>
}

export interface NetworkHistory {
  time: string
  upload: number
  download: number
}

export interface MetricHistory {
  time: string
  value: number
}

export interface ServerStore {
  serverList: Server[]
  currentMetrics: ServerMetrics | null
  cpuUsageHistory: MetricHistory[]
  memoryUsageHistory: MetricHistory[]
  diskUsageHistory: MetricHistory[]
  networkHistory: NetworkHistory[]
  loading: {
    servers: boolean
    metrics: boolean
    batch: boolean
  }
  error: string | null
} 