// 日志级别类型
export type LogLevel = 'info' | 'warning' | 'error' | 'debug'

// 日志来源类型
export type LogSource = 'master' | 'slave' | 'device' | 'user' | 'system'

// 日志记录接口
export interface LogRecord {
    id: string
    timestamp: string
    level: LogLevel
    message: string
    source: LogSource
    details?: Record<string, any>
    slaveId?: string
    deviceId?: string
    userId?: string
}

// 日志查询参数
export interface LogQuery {
    page: number
    pageSize: number
    startTime?: string
    endTime?: string
    level?: LogLevel
    source?: LogSource
    keyword?: string
    slaveId?: string
    deviceId?: string
    userId?: string
}

// 日志统计数据
export interface LogStats {
    totalLogs: number
    errorCount: number
    warningCount: number
    bySource: Record<LogSource, number>
    byLevel: Record<LogLevel, number>
    timeDistribution: Array<{
        timestamp: string
        count: number
    }>
}

// 日志响应接口
export interface LogResponse {
    code: number
    message: string
    data: {
        total: number
        items: LogRecord[]
        stats?: LogStats
    }
} 