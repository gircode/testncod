export interface User {
  id: number
  username: string
  role: string
  email: string
  organization: string
  is_active: boolean
  created_at: string
  updated_at: string
  permissions?: string[]
}

export interface LoginForm {
  username: string
  password: string
  client_type?: string
}

export interface RegisterForm {
  username: string
  password: string
  email: string
  organization: string
  mac_address?: string
}

export interface ResetPasswordForm {
  email: string
  code: string
  password: string
  confirm_password: string
}

export interface ForgotPasswordForm {
  email: string
}

export interface LoginResponse {
  token: string
  user: User
}

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
} 