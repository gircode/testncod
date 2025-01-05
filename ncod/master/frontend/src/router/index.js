import Monitor from '@/views/Monitor.vue'

export const routes = [
  {
    path: '/monitor',
    name: 'Monitor',
    component: Monitor,
    meta: {
      title: '系统监控',
      icon: 'Monitor',
      requiresAuth: true
    }
  }
  // ... 其他路由配置
] 