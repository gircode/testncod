import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

export class AppError extends Error {
  code?: string
  status?: number
  
  constructor(message: string, code?: string, status?: number) {
    super(message)
    this.code = code
    this.status = status
  }
}

export function setupErrorHandler() {
  const router = useRouter()
  const userStore = useUserStore()
  
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason
    
    if (error.status === 401) {
      userStore.logout()
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if (error.status === 403) {
      ElMessage.error('没有操作权限')
    } else {
      ElMessage.error(error.message || '操作失败')
    }
  })
  
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error)
    ElMessage.error('系统错误，请稍后重试')
  })
} 