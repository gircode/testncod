import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

interface UserInfo {
  id: number
  username: string
  role: string
  email: string
  organization: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const login = async (credentials: { username: string; password: string }) => {
    try {
      const response = await request.post('/auth/login', credentials)
      console.log('登录响应:', response)
      
      if (response.data.code !== 0 || !response.data.data) {
        throw new Error(response.data.message || '登录失败')
      }
      
      const { token: newToken, user } = response.data.data
      token.value = newToken
      userInfo.value = user
      
      localStorage.setItem('token', newToken)
      
      return response.data
    } catch (error: any) {
      console.error('登录失败:', error)
      throw error
    }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('password')
    localStorage.removeItem('remember')
    router.push('/auth/login')
  }

  return {
    token,
    userInfo,
    login,
    logout
  }
}) 