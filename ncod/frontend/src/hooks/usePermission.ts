import { useUserStore } from '@/stores/user'

export function usePermission() {
  const userStore = useUserStore()

  const hasPermission = (permission: string | string[]): boolean => {
    if (!userStore.user) return false

    const userPermissions = userStore.user.permissions || []
    if (typeof permission === 'string') {
      return userPermissions.includes(permission)
    }
    return permission.some(p => userPermissions.includes(p))
  }

  const hasRole = (role: string | string[]): boolean => {
    if (!userStore.user) return false

    const userRole = userStore.user.role
    if (typeof role === 'string') {
      return userRole === role
    }
    return role.includes(userRole)
  }

  const isAdmin = (): boolean => {
    return hasRole('admin')
  }

  const isSuperAdmin = (): boolean => {
    return hasRole('super_admin')
  }

  return {
    hasPermission,
    hasRole,
    isAdmin,
    isSuperAdmin
  }
} 