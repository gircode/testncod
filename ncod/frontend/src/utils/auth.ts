const TOKEN_KEY = 'ncod_token'

// 获取token
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

// 设置token
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

// 移除token
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

// 检查是否已登录
export const isAuthenticated = (): boolean => {
  return !!getToken()
} 