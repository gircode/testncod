import type { Directive, DirectiveBinding } from 'vue'
import { useAuthStore } from '@/store/auth'

function checkPermission(el: HTMLElement, binding: DirectiveBinding) {
  const { value } = binding
  const authStore = useAuthStore()
  const { user } = authStore

  if (value && typeof value === 'string') {
    const requiredRole = value
    const hasPermission = user?.role === requiredRole

    if (!hasPermission) {
      el.parentNode?.removeChild(el)
    }
  } else if (value && value instanceof Array) {
    const requiredRoles = value
    const hasPermission = user && requiredRoles.includes(user.role)

    if (!hasPermission) {
      el.parentNode?.removeChild(el)
    }
  } else {
    throw new Error('The permission directive value must be a string or an array of strings')
  }
}

const permission: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    checkPermission(el, binding)
  },

  updated(el: HTMLElement, binding: DirectiveBinding) {
    checkPermission(el, binding)
  }
}

export default permission 