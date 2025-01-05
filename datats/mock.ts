import { users, devices, slaves } from './data'
import type { LoginResponse, ListResponse, Device, Slave } from './types'

export const mockAuth = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const user = users.find(u => u.username === username)
    if (!user) {
      return { code: 1, message: '用户不存在', data: null }
    }
    if (password !== user.password) {
      return { code: 1, message: '密码错误', data: null }
    }
    return {
      code: 0,
      message: 'success',
      data: {
        token: 'mock_token_' + user.id,
        user: {
          id: user.id,
          username: user.username,
          role: user.role,
          email: user.email,
          organization: user.organization,
          is_active: user.is_active,
          created_at: user.created_at,
          updated_at: user.updated_at
        }
      }
    }
  }
}

export const mockDevice = {
  async getDeviceList(): Promise<ListResponse<Device>> {
    return {
      code: 0,
      message: 'success',
      data: {
        items: devices,
        total: devices.length
      }
    }
  }
}

export const mockSlave = {
  async getSlaveList(): Promise<ListResponse<Slave>> {
    return {
      code: 0,
      message: 'success',
      data: {
        items: slaves,
        total: slaves.length
      }
    }
  }
} 