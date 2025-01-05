import type { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import Message from './message'

interface RetryConfig extends AxiosRequestConfig {
  retryCount?: number
  retryDelay?: number
  shouldRetry?: (error: AxiosError) => boolean
  onRetry?: (retryCount: number, error: AxiosError) => void
}

interface RetryState {
  retryCount: number
  lastError?: AxiosError
}

export class RetryService {
  private static readonly DEFAULT_RETRY_COUNT = 3
  private static readonly DEFAULT_RETRY_DELAY = 1000
  private static readonly MAX_RETRY_DELAY = 10000

  private static retryStates = new Map<string, RetryState>()
  private static offlineQueue: Array<{
    config: RetryConfig
    resolve: (value: AxiosResponse) => void
    reject: (error: any) => void
  }> = []

  private static isOnline = navigator.onLine

  constructor() {
    this.setupNetworkListeners()
  }

  private setupNetworkListeners() {
    window.addEventListener('online', this.handleOnline.bind(this))
    window.addEventListener('offline', this.handleOffline.bind(this))
  }

  private handleOnline() {
    RetryService.isOnline = true
    Message.success('网络已恢复')
    this.processOfflineQueue()
  }

  private handleOffline() {
    RetryService.isOnline = false
    Message.warning('网络已断开')
  }

  private async processOfflineQueue() {
    const queue = [...RetryService.offlineQueue]
    RetryService.offlineQueue = []

    for (const item of queue) {
      try {
        const response = await this.executeRequest(item.config)
        item.resolve(response)
      } catch (error) {
        item.reject(error)
      }
    }
  }

  /**
   * 生成请求的唯一标识
   */
  private static getRequestKey(config: AxiosRequestConfig): string {
    const { method, url, params, data } = config
    return `${method}-${url}-${JSON.stringify(params)}-${JSON.stringify(data)}`
  }

  /**
   * 判断是否应该重试请求
   */
  private static shouldRetry(error: AxiosError, config: RetryConfig): boolean {
    if (config.shouldRetry) {
      return config.shouldRetry(error)
    }

    // 默认重试条件
    const status = error.response?.status
    return (
      !error.response || // 网络错误
      status === 408 || // 请求超时
      status === 429 || // 太多请求
      status === 500 || // 服务器错误
      status === 502 || // 网关错误
      status === 503 || // 服务不可用
      status === 504 // 网关超时
    )
  }

  /**
   * 计算重试延迟时间（指数退避）
   */
  private static getRetryDelay(retryCount: number, config: RetryConfig): number {
    const baseDelay = config.retryDelay || RetryService.DEFAULT_RETRY_DELAY
    const delay = Math.min(
      baseDelay * Math.pow(2, retryCount - 1) + Math.random() * 1000,
      RetryService.MAX_RETRY_DELAY
    )
    return delay
  }

  /**
   * 执行请求
   */
  private async executeRequest(config: RetryConfig): Promise<AxiosResponse> {
    const axios = (await import('axios')).default
    return axios(config)
  }

  /**
   * 处理请求重试
   */
  public async handleRequest(config: RetryConfig): Promise<AxiosResponse> {
    const requestKey = RetryService.getRequestKey(config)
    const maxRetries = config.retryCount || RetryService.DEFAULT_RETRY_COUNT

    if (!RetryService.isOnline) {
      return new Promise((resolve, reject) => {
        RetryService.offlineQueue.push({ config, resolve, reject })
      })
    }

    try {
      const response = await this.executeRequest(config)
      // 请求成功，清除重试状态
      RetryService.retryStates.delete(requestKey)
      return response
    } catch (error: any) {
      const state = RetryService.retryStates.get(requestKey) || { retryCount: 0 }
      state.lastError = error

      if (state.retryCount < maxRetries && RetryService.shouldRetry(error, config)) {
        state.retryCount++
        RetryService.retryStates.set(requestKey, state)

        // 触发重试回调
        if (config.onRetry) {
          config.onRetry(state.retryCount, error)
        }

        // 等待重试延迟
        const delay = RetryService.getRetryDelay(state.retryCount, config)
        await new Promise(resolve => setTimeout(resolve, delay))

        // 重试请求
        return this.handleRequest(config)
      }

      // 达到最大重试次数或不应该重试，抛出最后一个错误
      throw state.lastError
    }
  }

  /**
   * 重置请求的重试状态
   */
  public resetRetryState(config: AxiosRequestConfig) {
    const requestKey = RetryService.getRequestKey(config)
    RetryService.retryStates.delete(requestKey)
  }

  /**
   * 清除所有重试状态
   */
  public clearAllRetryStates() {
    RetryService.retryStates.clear()
  }

  /**
   * 获取请求的重试状态
   */
  public getRetryState(config: AxiosRequestConfig): RetryState | undefined {
    const requestKey = RetryService.getRequestKey(config)
    return RetryService.retryStates.get(requestKey)
  }
}

export default new RetryService() 