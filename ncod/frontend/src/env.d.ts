/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'vue' {
  import { ref, reactive, onMounted } from '@vue/runtime-dom'
  export { ref, reactive, onMounted }
  export * from '@vue/runtime-dom'
}

declare module '@/store/auth' {
  import { UserInfo } from '@/mock/types'
  
  export interface AuthStore {
    token: string
    userInfo: UserInfo | null
    login: (credentials: { username: string; password: string }) => Promise<any>
    logout: () => void
  }
  
  export function useAuthStore(): AuthStore
} 