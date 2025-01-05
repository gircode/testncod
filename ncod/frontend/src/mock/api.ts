import { MockMethod } from 'vite-plugin-mock'
import type { User } from '@/types/api'

const users: User[] = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
]

export default [
  {
    url: '/api/auth/login',
    method: 'post',
    response: ({ body }) => {
      const { username, password } = body
      const user = users.find(u => u.username === username)
      
      if (user && password === '123456') {
        return {
          code: 200,
          message: '登录成功',
          data: {
            token: 'mock_token_' + Date.now(),
            refreshToken: 'mock_refresh_token_' + Date.now(),
            user
          }
        }
      }
      
      return {
        code: 401,
        message: '用户名或密码错误',
        data: null
      }
    }
  }
] as MockMethod[]