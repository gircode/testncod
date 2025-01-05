import request from '@/utils/request'
import type { LoginResponse, RegisterForm, ApiResponse } from '@/types/user'

export const login = (data: { username?: string; password?: string; macAddress?: string }) => {
  return request.post<ApiResponse<LoginResponse>>('/auth/login', data)
}

export const register = (data: RegisterForm) => {
  return request.post<ApiResponse<void>>('/auth/register', data)
}
