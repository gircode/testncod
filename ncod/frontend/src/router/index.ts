import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/monitoring',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'monitoring',
        name: 'Monitoring',
        component: () => import('@/views/monitoring/index.vue'),
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: '/auth',
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/Login.vue')
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/Register.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/auth/login')
  } else if (to.path === '/auth/login' && token) {
    // 如果已登录且访问登录页，重定向到首页
    next('/')
  } else {
    next()
  }
})

export default router
