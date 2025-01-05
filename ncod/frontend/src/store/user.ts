import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface User {
  id: number
  username: string
  email: string
  phone: string
  role: string
  status: string
  remark?: string
  createdAt: string
  updatedAt: string
}

export interface UserListParams {
  page: number
  pageSize: number
  username?: string
  role?: string
  status?: string
}

export interface UserListResponse {
  data: User[]
  total: number
}

export const useUserStore = defineStore('user', () => {
  const loading = ref(false)
  const currentUser = ref<User | null>(null)

  // 获取用户列表
  const getUserList = async (params: UserListParams): Promise<UserListResponse> => {
    try {
      const response = await axios.get('/api/users', { params })
      return response.data
    } catch (error) {
      throw new Error('获取用户列表失败')
    }
  }

  // 创建用户
  const createUser = async (user: Omit<User, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      const response = await axios.post('/api/users', user)
      return response.data
    } catch (error) {
      throw new Error('创建用户失败')
    }
  }

  // 更新用户
  const updateUser = async (id: number, user: Partial<User>) => {
    try {
      const response = await axios.put(`/api/users/${id}`, user)
      return response.data
    } catch (error) {
      throw new Error('更新用户失败')
    }
  }

  // 删除用户
  const deleteUser = async (id: number) => {
    try {
      await axios.delete(`/api/users/${id}`)
    } catch (error) {
      throw new Error('删除用户失败')
    }
  }

  // 重置用户密码
  const resetUserPassword = async (id: number, newPassword: string) => {
    try {
      await axios.post(`/api/users/${id}/reset-password`, { newPassword })
    } catch (error) {
      throw new Error('重置密码失败')
    }
  }

  // 更新用户状态
  const updateUserStatus = async (id: number, status: string) => {
    try {
      await axios.put(`/api/users/${id}/status`, { status })
    } catch (error) {
      throw new Error('更新用户状态失败')
    }
  }

  return {
    loading,
    currentUser,
    getUserList,
    createUser,
    updateUser,
    deleteUser,
    resetUserPassword,
    updateUserStatus
  }
}) 