import request from '@/utils/request'
import type { User, ApiResponse } from '@/types/auth'

export interface UserQueryParams {
  keyword?: string
  page?: number
  limit?: number
  role?: string
  is_active?: boolean
}

export interface UserCreateParams {
  username: string
  email: string
  password: string
  organization: string
  role: 'admin' | 'user'
  is_active: boolean
  mac_address?: string
}

export interface UserUpdateParams extends Partial<Omit<UserCreateParams, 'password'>> {
  id: number
}

// 获取用户列表
export const getUserList = (params: UserQueryParams) => {
  return request.get<ApiResponse<{ items: User[]; total: number }>>('/api/users', { params })
}

// 获取用户详情
export const getUserDetail = (id: number) => {
  return request.get<ApiResponse<User>>(`/api/users/${id}`)
}

// 创建用户
export const createUser = (data: UserCreateParams) => {
  return request.post<ApiResponse<User>>('/api/users', data)
}

// 更新用户
export const updateUser = (id: number, data: UserUpdateParams) => {
  return request.put<ApiResponse<User>>(`/api/users/${id}`, data)
}

// 删除用户
export const deleteUser = (id: number) => {
  return request.delete<ApiResponse<void>>(`/api/users/${id}`)
}

// 修改用户状态
export const updateUserStatus = (id: number, is_active: boolean) => {
  return request.patch<ApiResponse<User>>(`/api/users/${id}/status`, { is_active })
}

// 重置用户密码
export const resetUserPassword = (id: number) => {
  return request.post<ApiResponse<{ password: string }>>(`/api/users/${id}/reset-password`)
}

// 修改用户密码
export const changeUserPassword = (id: number, old_password: string, new_password: string) => {
  return request.post<ApiResponse<void>>(`/api/users/${id}/change-password`, {
    old_password,
    new_password
  })
}

// 导出用户列表
export const exportUserList = (params: UserQueryParams) => {
  return request.get('/api/users/export', {
    params,
    responseType: 'blob'
  })
}

// 导入用户
export const importUsers = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<ApiResponse<{ success: number; failed: number }>>('/api/users/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
} 