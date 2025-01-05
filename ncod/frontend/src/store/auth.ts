import { defineStore } from 'pinia'
import type { UserInfo, RegisterForm } from '@/types/user'
import { login as loginApi, register as registerApi } from '@/api/auth'
import router from '@/router'

interface State {
  token: string | null
  userInfo: UserInfo | null
}

interface Actions {
  login: (formData: { username: string; password: string; captcha: string; remember?: boolean }) => Promise<boolean>
  register: (formData: RegisterForm) => Promise<boolean>
  logout: () => void
}

export type AuthStore = State & Actions

export const useAuthStore = defineStore('auth', {
  state: (): State => ({
    token: null,
    userInfo: null
  }),

  actions: {
    async login(formData: { username: string; password: string; captcha: string; remember?: boolean }): Promise<boolean> {
      try {
        const response = await loginApi(formData)
        if (response.data.code === 0 && response.data.data) {
          this.token = response.data.data.token
          this.userInfo = response.data.data.userInfo
          localStorage.setItem('token', response.data.data.token)
          router.push('/monitoring')
          return true
        }
        return false
      } catch (error) {
        console.error('Login failed:', error)
        return false
      }
    },

    async register(formData: RegisterForm): Promise<boolean> {
      try {
        const response = await registerApi(formData)
        return response.data.code === 0
      } catch (error) {
        console.error('Registration failed:', error)
        return false
      }
    },

    logout(): void {
      this.token = null
      this.userInfo = null
      localStorage.removeItem('token')
      router.push('/auth/login')
    },

    async loginByMac(macAddress: string): Promise<boolean> {
      try {
        const response = await loginApi({ macAddress })
        if (response.data.code === 0 && response.data.data) {
          this.token = response.data.data.token
          this.userInfo = response.data.data.userInfo
          localStorage.setItem('token', response.data.data.token)
          router.push('/monitoring')
          return true
        }
        return false
      } catch (error) {
        console.error('MAC login failed:', error)
        return false
      }
    }
  }
})
