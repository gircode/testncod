// 主服务器状态类型
export type MasterStatus = 'running' | 'stopped' | 'error'

// 主服务器信息
export interface MasterInfo {
    id: string
    name: string
    version: string
    status: MasterStatus
    startTime: string
    uptime: number
    nodeCount: number
    deviceCount: number
    userCount: number
}

// 主服务器性能指标
export interface MasterMetrics {
    cpuUsage: number
    memoryUsage: number
    diskUsage: number
    networkIn: number
    networkOut: number
    activeConnections: number
    requestsPerSecond: number
    errorRate: number
}

// 从服务器信息
export interface SlaveInfo {
    id: string
    name: string
    ip: string
    port: number
    status: 'online' | 'offline'
    lastHeartbeat: string
    deviceCount: number
}

// 主服务器设置
export interface MasterSettings {
    name: string
    description?: string
    maxSlaves: number
    maxDevicesPerSlave: number
    heartbeatInterval: number
    performanceSettings: {
        cpuThreshold: number
        memoryThreshold: number
        diskThreshold: number
        networkThreshold: number
    }
    securitySettings: {
        enableSSL: boolean
        sslCertPath?: string
        sslKeyPath?: string
        enableFirewall: boolean
        allowedIPs: string[]
    }
    notificationSettings: {
        enableEmail: boolean
        emailConfig?: {
            smtpServer: string
            smtpPort: number
            username: string
            password: string
            fromAddress: string
            toAddresses: string[]
        }
        enableWebhook: boolean
        webhookUrl?: string
    }
}

// 系统统计数据
export interface SystemStats {
    onlineSlaves: number
    onlineDevices: number
    activeUsers: number
    totalRequests: number
    errorCount: number
    avgResponseTime: number
    cpuUsage: number
    memoryUsage: number
    diskUsage: number
} 