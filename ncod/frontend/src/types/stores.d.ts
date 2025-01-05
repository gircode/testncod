import { User } from './auth'

export interface UserState {
  user: User | null
  token: string | null
  permissions: string[]
}

export interface UserStore extends UserState {
  login: (data: { username: string; password: string }) => Promise<any>
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  clearUser: () => void
  hasPermission: (permission: string | string[]) => boolean
} 