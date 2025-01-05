import { defineStore } from 'pinia'
import { ref } from '@vue/runtime-core'
import { mockAuth } from '@/mock'
import type { User as AuthUser } from '@/mock/types'

export interface User extends AuthUser {
  permissions: string[]
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const permissions = ref<string[]>([])

  async function login(data: { username: string; password: string }) {
    try {
      if (!data.username || !data.password) {
        throw new Error('用户名和密码不能为空')
      }

      console.log('开始登录请求:', data)
      const res = await mockAuth.login(data.username, data.password)
      console.log('登录响应:', res)

      if (res.code !== 0 || !res.data) {
        throw new Error(res.message || '登录失败')
      }

      const loginData = res.data
      console.log('设置token:', loginData.token)
      setToken(loginData.token)
      
      console.log('设置用户信息:', loginData.user)
      setUser({
        ...loginData.user,
        permissions: loginData.user.role === 'admin' ? ['*'] : []
      })
      
      return loginData
    } catch (error: any) {
      console.error('登录错误:', error)
      clearUser()
      throw error
    }
  }

  function setUser(newUser: User | null) {
    user.value = newUser
    if (newUser) {
      permissions.value = newUser.permissions
    } else {
      permissions.value = []
    }
  }

  function setToken(newToken: string | null) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }

  function clearUser() {
    user.value = null
    token.value = null
    permissions.value = []
    localStorage.removeItem('token')
  }

  function hasPermission(permission: string | string[]): boolean {
    if (!permissions.value) return false
    
    if (permissions.value.includes('*')) return true
    
    if (typeof permission === 'string') {
      return permissions.value.includes(permission)
    }
    
    return permission.some(p => permissions.value.includes(p))
  }

  // 初始化时检查是否有保存的token
  const initToken = localStorage.getItem('token')
  if (initToken) {
    setToken(initToken)
  }

  return {
    user,
    token,
    permissions,
    login,
    setUser,
    setToken,
    clearUser,
    hasPermission
  }
}) 