<template>
  <div class="min-h-screen bg-gray-100">
    <!-- 侧边栏 -->
    <nav
      class="fixed top-0 left-0 bottom-0 flex flex-col w-64 bg-gray-800 text-white transition-all duration-300"
      :class="{ '-translate-x-full': !sidebarOpen }"
    >
      <div class="flex items-center justify-between h-16 px-4 bg-gray-900">
        <span class="text-xl font-semibold">NCOD 系统</span>
        <button
          class="p-1 rounded-md hover:bg-gray-700 lg:hidden"
          @click="toggleSidebar"
        >
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div class="px-2 py-4 space-y-1">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center px-4 py-2 text-sm rounded-md hover:bg-gray-700"
            :class="{ 'bg-gray-700': isCurrentRoute(item.path) }"
          >
            <component :is="item.icon" class="w-5 h-5 mr-3" />
            {{ item.name }}
          </router-link>
        </div>
      </div>

      <div class="p-4 border-t border-gray-700">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium">{{ user?.username }}</p>
            <p class="text-xs text-gray-400">{{ user?.role === 'admin' ? '管理员' : '普通用户' }}</p>
          </div>
        </div>
        <button
          class="mt-4 w-full flex items-center justify-center px-4 py-2 text-sm rounded-md bg-gray-700 hover:bg-gray-600"
          @click="handleLogout"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
          退出登录
        </button>
      </div>
    </nav>

    <!-- 主内容区 -->
    <div class="lg:pl-64">
      <!-- 顶部导航栏 -->
      <div class="fixed top-0 right-0 left-0 lg:left-64 z-10">
        <div class="flex items-center justify-between h-16 px-4 bg-white shadow-sm">
          <button
            class="p-1 rounded-md text-gray-500 hover:text-gray-900 lg:hidden"
            @click="toggleSidebar"
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          <div class="flex items-center">
            <span class="text-gray-500">{{ currentDateTime }}</span>
          </div>
        </div>
      </div>

      <!-- 页面内容 -->
      <main class="px-4 py-20">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const sidebarOpen = ref(true)
const currentDateTime = ref(new Date().toLocaleString())
let timer: number

// 菜单项配置
const menuItems = [
  {
    name: '监控面板',
    path: '/monitoring',
    icon: 'ChartBarIcon',
  },
  {
    name: '用户管理',
    path: '/users',
    icon: 'UsersIcon',
  },
  {
    name: '设备管理',
    path: '/devices',
    icon: 'DeviceIcon',
  },
  {
    name: '系统设置',
    path: '/settings',
    icon: 'CogIcon',
  },
]

// 计算属性
const user = computed(() => authStore.user)

// 方法
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const isCurrentRoute = (path: string) => {
  return route.path.startsWith(path)
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/auth/login')
  } catch (error) {
    console.error('Logout failed:', error)
  }
}

const updateDateTime = () => {
  currentDateTime.value = new Date().toLocaleString()
}

// 生命周期钩子
onMounted(() => {
  // 每秒更新一次时间
  timer = window.setInterval(updateDateTime, 1000)
})

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 