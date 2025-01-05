import { useAuthStore } from '@/store/auth'
import request from '@/utils/request'
import type { ApiResponse } from '@/types/auth'

interface LogData {
  type: 'info' | 'warning' | 'error'
  module: string
  action: string
  details?: Record<string, any>
  timestamp?: string
}

interface LogEntry extends LogData {
  user_id: number
  username: string
  ip_address?: string
  user_agent?: string
}

class Logger {
  private queue: LogEntry[] = []
  private batchSize: number = 10
  private flushInterval: number = 5000 // 5秒
  private timer: number | null = null
  private isProcessing: boolean = false

  constructor() {
    this.startTimer()
    window.addEventListener('beforeunload', () => this.flush())
  }

  private startTimer() {
    this.timer = window.setInterval(() => {
      this.flush()
    }, this.flushInterval)
  }

  private stopTimer() {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
  }

  private async flush() {
    if (this.isProcessing || this.queue.length === 0) return

    try {
      this.isProcessing = true
      const logs = this.queue.splice(0, this.batchSize)
      await this.sendLogs(logs)
    } catch (error) {
      console.error('Failed to send logs:', error)
      // 失败时将日志放回队列
      this.queue.unshift(...this.queue.splice(0, this.batchSize))
    } finally {
      this.isProcessing = false
    }
  }

  private async sendLogs(logs: LogEntry[]) {
    await request.post<ApiResponse<void>>('/api/logs/batch', { logs })
  }

  private enrichLogData(data: LogData): LogEntry {
    const authStore = useAuthStore()
    const user = authStore.user

    if (!user) {
      throw new Error('User not authenticated')
    }

    return {
      ...data,
      user_id: user.id,
      username: user.username,
      timestamp: new Date().toISOString(),
      ip_address: window.location.hostname,
      user_agent: navigator.userAgent
    }
  }

  public log(data: LogData) {
    try {
      const enrichedLog = this.enrichLogData(data)
      this.queue.push(enrichedLog)

      // 如果队列达到批处理大小，立即发送
      if (this.queue.length >= this.batchSize) {
        this.flush()
      }

      // 开发环境下在控制台输出日志
      if (import.meta.env.DEV) {
        console.log('[Logger]', enrichedLog)
      }
    } catch (error) {
      console.error('Failed to create log:', error)
    }
  }

  public info(module: string, action: string, details?: Record<string, any>) {
    this.log({ type: 'info', module, action, details })
  }

  public warning(module: string, action: string, details?: Record<string, any>) {
    this.log({ type: 'warning', module, action, details })
  }

  public error(module: string, action: string, details?: Record<string, any>) {
    this.log({ type: 'error', module, action, details })
  }
}

export default new Logger() 