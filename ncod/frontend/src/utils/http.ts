import { message } from 'ant-design-vue'

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>
}

interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

const BASE_URL = '/api'

class Http {
  private static instance: Http
  private token: string | null = null

  private constructor() {
    // 从localStorage获取token
    this.token = localStorage.getItem('token')
  }

  static getInstance(): Http {
    if (!Http.instance) {
      Http.instance = new Http()
    }
    return Http.instance
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('token')
  }

  private async request<T>(url: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const { params, ...restOptions } = options
    let fullUrl = `${BASE_URL}${url}`

    // 处理URL参数
    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        fullUrl += `?${queryString}`
      }
    }

    // 添加默认headers
    const headers = new Headers(options.headers)
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`)
    }

    try {
      const response = await fetch(fullUrl, {
        ...restOptions,
        headers
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: ApiResponse<T> = await response.json()

      // 处理业务错误
      if (data.code !== 0) {
        message.error(data.message || '请求失败')
        throw new Error(data.message)
      }

      return data
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('网络请求失败')
      }
      throw error
    }
  }

  async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    const response = await this.request<T>(url, { method: 'GET', params })
    return response.data
  }

  async post<T>(url: string, data?: any, params?: Record<string, any>): Promise<T> {
    const response = await this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      params
    })
    return response.data
  }

  async put<T>(url: string, data?: any, params?: Record<string, any>): Promise<T> {
    const response = await this.request<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      params
    })
    return response.data
  }

  async delete<T>(url: string, params?: Record<string, any>): Promise<T> {
    const response = await this.request<T>(url, { method: 'DELETE', params })
    return response.data
  }
}

export const http = Http.getInstance() 