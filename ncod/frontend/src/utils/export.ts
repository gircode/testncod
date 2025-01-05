import { saveAs } from 'file-saver'
import { formatBytes, formatBitrate, formatIOPS, formatDuration } from './performance'
import type { ServerMetrics, ServerPerformance } from '@/types/server'

interface ExportOptions {
    timeRange: string
    metrics: string[]
    format: 'csv' | 'json' | 'excel'
}

export class ExportService {
    // 生成CSV数据
    private static generateCSV(data: ServerPerformance[], metrics: string[]): string {
        const headers = ['时间戳']
        const rows: string[][] = []

        // 添加指标列
        metrics.forEach(metric => {
            switch (metric) {
                case 'cpu':
                    headers.push('CPU使用率(%)', 'CPU温度(°C)', '1分钟负载', '5分钟负载', '15分钟负载')
                    break
                case 'memory':
                    headers.push('内存使用率(%)', '已用内存', '空闲内存', '缓存内存')
                    break
                case 'disk':
                    headers.push('磁盘使用率(%)', '读取速度', '写入速度', 'IOPS')
                    break
                case 'network':
                    headers.push('入站流量', '出站流量', '连接数')
                    break
            }
        })

        // 添加数据行
        data.forEach(record => {
            const row = [record.timestamp]
            metrics.forEach(metric => {
                switch (metric) {
                    case 'cpu':
                        row.push(
                            record.cpuUsage.toString(),
                            record.cpuTemperature?.toString() || '0',
                            record.loadAvg1.toString(),
                            record.loadAvg5.toString(),
                            record.loadAvg15.toString()
                        )
                        break
                    case 'memory':
                        row.push(
                            record.memoryUsage.toString(),
                            formatBytes(record.memoryUsed || 0),
                            formatBytes(record.memoryFree || 0),
                            formatBytes(record.memoryCached || 0)
                        )
                        break
                    case 'disk':
                        row.push(
                            record.diskUsage.toString(),
                            formatBytes(record.diskRead),
                            formatBytes(record.diskWrite),
                            formatIOPS(record.diskIOPS || 0)
                        )
                        break
                    case 'network':
                        row.push(
                            formatBitrate(record.networkIn),
                            formatBitrate(record.networkOut),
                            record.networkConnections?.toString() || '0'
                        )
                        break
                }
            })
            rows.push(row)
        })

        // 生成CSV内容
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n')

        return csvContent
    }

    // 生成JSON数据
    private static generateJSON(data: ServerPerformance[], metrics: string[]): string {
        const filteredData = data.map(record => {
            const filtered: any = {
                timestamp: record.timestamp
            }

            metrics.forEach(metric => {
                switch (metric) {
                    case 'cpu':
                        filtered.cpu = {
                            usage: record.cpuUsage,
                            temperature: record.cpuTemperature,
                            loadAvg: [record.loadAvg1, record.loadAvg5, record.loadAvg15]
                        }
                        break
                    case 'memory':
                        filtered.memory = {
                            usage: record.memoryUsage,
                            used: record.memoryUsed,
                            free: record.memoryFree,
                            cached: record.memoryCached
                        }
                        break
                    case 'disk':
                        filtered.disk = {
                            usage: record.diskUsage,
                            read: record.diskRead,
                            write: record.diskWrite,
                            iops: record.diskIOPS
                        }
                        break
                    case 'network':
                        filtered.network = {
                            in: record.networkIn,
                            out: record.networkOut,
                            connections: record.networkConnections
                        }
                        break
                }
            })

            return filtered
        })

        return JSON.stringify(filteredData, null, 2)
    }

    // 导出数据
    public static async exportData(
        serverName: string,
        data: ServerPerformance[],
        options: ExportOptions
    ): Promise<void> {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
        const fileName = `${serverName}_metrics_${timestamp}`

        let content: string
        let mimeType: string
        let fileExtension: string

        switch (options.format) {
            case 'csv':
                content = this.generateCSV(data, options.metrics)
                mimeType = 'text/csv;charset=utf-8'
                fileExtension = 'csv'
                break
            case 'json':
                content = this.generateJSON(data, options.metrics)
                mimeType = 'application/json;charset=utf-8'
                fileExtension = 'json'
                break
            case 'excel':
                // TODO: 实现Excel导出
                throw new Error('Excel导出功能尚未实现')
            default:
                throw new Error('不支持的导出格式')
        }

        const blob = new Blob([content], { type: mimeType })
        saveAs(blob, `${fileName}.${fileExtension}`)
    }

    // 生成性能报告
    public static generateReport(metrics: ServerMetrics): string {
        const sections = []

        // CPU部分
        sections.push(`CPU性能报告
------------------------
使用率: ${metrics.cpu.usage}%
核心数: ${metrics.cpu.cores}
温度: ${metrics.cpu.temperature}°C
进程数: ${metrics.cpu.processes}
系统负载: ${metrics.cpu.loadAvg.join(', ')}
`)

        // 内存部分
        sections.push(`内存使用情况
------------------------
总内存: ${formatBytes(metrics.memory.total)}
已用内存: ${formatBytes(metrics.memory.used)}
空闲内存: ${formatBytes(metrics.memory.free)}
缓存: ${formatBytes(metrics.memory.cached)}
缓冲区: ${formatBytes(metrics.memory.buffers)}
Swap总量: ${formatBytes(metrics.memory.swapTotal)}
Swap使用: ${formatBytes(metrics.memory.swapUsed)}
`)

        // 磁盘部分
        sections.push(`磁盘性能
------------------------
总容量: ${formatBytes(metrics.disk.total)}
已用空间: ${formatBytes(metrics.disk.used)}
可用空间: ${formatBytes(metrics.disk.free)}
读取速度: ${formatBytes(metrics.disk.readSpeed)}/s
写入速度: ${formatBytes(metrics.disk.writeSpeed)}/s
IOPS: ${formatIOPS(metrics.disk.iops)}
`)

        // 网络部分
        sections.push(`网络性能
------------------------
当前连接数: ${metrics.network.connections}
入站带宽: ${formatBitrate(metrics.network.bandwidth.in)}
出站带宽: ${formatBitrate(metrics.network.bandwidth.out)}

网络接口统计:
${metrics.network.interfaces.map(iface => `
${iface.name}:
  接收: ${formatBytes(iface.bytesIn)}
  发送: ${formatBytes(iface.bytesOut)}
  数据包(接收/发送): ${iface.packetsIn}/${iface.packetsOut}
  错误: ${iface.errors}
  丢包: ${iface.drops}
`).join('\n')}
`)

        // 系统信息部分
        sections.push(`系统信息
------------------------
运行时间: ${formatDuration(metrics.system.uptime)}
启动时间: ${metrics.system.bootTime}
进程数: ${metrics.system.processes}
线程数: ${metrics.system.threads}
在线用户: ${metrics.system.users}
`)

        return sections.join('\n\n')
    }
} 