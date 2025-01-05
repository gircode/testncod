import { message } from 'ant-design-vue'
import type { ApiResponse } from '@/types/api'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

interface RequestOptions extends RequestInit {
  timeout?: number
}

export async function request<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const { timeout = 10000, ...fetchOptions } = options
  
  // 添加默认headers
  const headers = new Headers(fetchOptions.headers)
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  
  // 添加token
  const token = localStorage.getItem('token')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  // 创建AbortController用于超时控制
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)
  
  try {
    const response = await fetch(`${BASE_URL}${url}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json() as ApiResponse<T>
    
    // 处理业务错误
    if (data.code !== 200) {
      message.error(data.message || '请求失败')
      throw new Error(data.message)
    }
    
    return data.data
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        message.error('请求超时')
      } else {
        message.error(error.message || '请求失败')
      }
    }
    throw error
  }
}
