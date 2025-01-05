// 用户角色类型
export type UserRole = 'admin' | 'manager' | 'user'

// 用户状态类型
export type UserStatus = 'active' | 'inactive' | 'pending'

// 用户信息接口
export interface UserInfo {
  id: number
  username: string
  role: UserRole
  email: string
  organization: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 登录响应
export interface LoginResponse {
  token: string
  userInfo: UserInfo
}

// 注册表单
export interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  organization?: string
}

// API 响应
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
} 