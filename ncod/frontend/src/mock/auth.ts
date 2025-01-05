import { MockMethod } from 'vite-plugin-mock'

interface MockRequest {
  body: {
    username: string
    password: string
    captcha: string
    email?: string
  }
}

const users = [
  {
    id: 1,
    username: 'admin',
    password: '123456',
    role: 'admin',
    email: 'admin@example.com',
    organization: 'NCOD',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    username: 'user1',
    password: '123456',
    role: 'user',
    email: 'user1@example.com',
    organization: 'NCOD',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
]

export default [
  {
    url: '/api/auth/captcha',
    method: 'get',
    response: () => {
      // 生成一个简单的base64图片验证码
      const captchaImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAABkCAYAAADDhn8LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABCSURBVHic7dAxAQAAAMKg9U9tDQ8gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgBwQYAAH2AAGAAAAAAElFTkSuQmCC';
      
      return {
        code: 0,
        message: 'success',
        data: {
          captcha: '1234',
          captchaImage
        }
      }
    }
  },
  {
    url: '/api/auth/login',
    method: 'post',
    response: ({ body }: MockRequest) => {
      const { username, password, captcha } = body
      
      if (captcha !== '1234') {
        return {
          code: -1,
          message: '验证码错误',
          data: null
        }
      }
      const user = users.find(u => u.username === username && u.password === password)

      if (user) {
        const { password: _, ...userWithoutPassword } = user
        return {
          code: 0,
          message: '登录成功',
          data: {
            token: `mock_token_${user.id}_${Date.now()}`,
            userInfo: userWithoutPassword
          }
        }
      }

      return {
        code: -1,
        message: '用户名或密码错误',
        data: null
      }
    }
  },
  {
    url: '/api/auth/register',
    method: 'post',
    response: ({ body }: MockRequest) => {
      const { username, email } = body
      
      if (!email) {
        return {
          code: -1,
          message: '邮箱不能为空',
          data: null
        }
      }
      
      if (users.some(u => u.username === username)) {
        return {
          code: -1,
          message: '用户名已存在',
          data: null
        }
      }

      if (users.some(u => u.email === email)) {
        return {
          code: -1,
          message: '邮箱已被使用',
          data: null
        }
      }

      const newUser = {
        id: users.length + 1,
        username,
        email,
        role: 'user',
        organization: 'NCOD',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      users.push({ ...newUser, password: body.password })

      return {
        code: 0,
        message: '注册成功',
        data: newUser
      }
    }
  }
] as MockMethod[]
