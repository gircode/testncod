// API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 登录响应数据类型
export interface LoginResponseData {
  code: number
  message: string
  data: {
    token: string
    refreshToken: string
    user: User
  }
}

// 用户信息类型
export interface User {
  id: number
  username: string
  email?: string
  role: string
  status: string
  created_at: string
  updated_at: string
}

// 登录请求参数类型
export interface LoginParams {
  username: string
  password: string
}

// 刷新token响应数据类型
export interface RefreshTokenResponse {
  token: string
  refreshToken: string
} 