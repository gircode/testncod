// API基础配置
const API_CONFIG = {
  // 开发环境API地址
  development: {
    baseURL: 'http://localhost:5000/api',
    timeout: 10000
  },
  // 生产环境API地址
  production: {
    baseURL: 'https://api.your-domain.com/api', // 需要替换为实际的生产环境API地址
    timeout: 10000
  }
}

// 获取当前环境
const ENV = import.meta.env.MODE

// 导出当前环境的配置
export const apiConfig = API_CONFIG[ENV as keyof typeof API_CONFIG] 