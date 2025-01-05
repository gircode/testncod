<template>
  <div class="space-y-6">
    <!-- 顶部操作栏 -->
    <div class="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
      <div class="md:flex md:items-center md:justify-between">
        <div class="flex-1 min-w-0">
          <h2 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">用户管理</h2>
        </div>
        <div class="mt-4 flex md:mt-0 md:ml-4">
          <button
            type="button"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            @click="handleRefresh"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            刷新
          </button>
          <button
            type="button"
            class="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            @click="showAddUserDialog = true"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            添加用户
          </button>
        </div>
      </div>

      <!-- 搜索栏 -->
      <div class="mt-4">
        <div class="flex rounded-md shadow-sm">
          <input
            type="text"
            v-model="searchQuery"
            class="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-l-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border-gray-300"
            placeholder="搜索用户名或邮箱..."
          />
          <button
            type="button"
            class="-ml-px relative inline-flex items-center space-x-2 px-4 py-2 border border-gray-300 text-sm font-medium rounded-r-md text-gray-700 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
            @click="handleSearch"
          >
            <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            搜索
          </button>
        </div>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="user in filteredUsers" :key="user.id">
          <div class="px-4 py-4 flex items-center sm:px-6">
            <div class="min-w-0 flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <div class="flex text-sm">
                  <p class="font-medium text-indigo-600 truncate">{{ user.username }}</p>
                  <p class="ml-1 flex-shrink-0 font-normal text-gray-500">
                    {{ user.email }}
                  </p>
                </div>
                <div class="mt-2 flex">
                  <div class="flex items-center text-sm text-gray-500">
                    <svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    {{ user.organization }}
                  </div>
                  <div class="ml-6 flex items-center text-sm text-gray-500">
                    <svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(user.created_at) }}
                  </div>
                </div>
              </div>
              <div class="mt-4 flex-shrink-0 sm:mt-0 sm:ml-5">
                <div class="flex -space-x-1 overflow-hidden">
                  <span
                    class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="{
                      'bg-green-100 text-green-800': user.is_active,
                      'bg-red-100 text-red-800': !user.is_active
                    }"
                  >
                    {{ user.is_active ? '激活' : '禁用' }}
                  </span>
                  <span
                    class="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800"
                  >
                    {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </div>
              </div>
            </div>
            <div class="ml-5 flex-shrink-0">
              <div class="flex space-x-2">
                <button
                  type="button"
                  class="inline-flex items-center p-2 border border-transparent rounded-full shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  @click="handleEdit(user)"
                >
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="inline-flex items-center p-2 border border-transparent rounded-full shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  @click="handleDelete(user)"
                >
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- 添加/编辑用户对话框 -->
    <div v-if="showAddUserDialog || showEditUserDialog" class="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <div class="mt-3 text-center sm:mt-5">
              <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                {{ showAddUserDialog ? '添加用户' : '编辑用户' }}
              </h3>
              <div class="mt-2">
                <form class="space-y-4" @submit.prevent="handleSubmit">
                  <div>
                    <label for="username" class="block text-sm font-medium text-gray-700">用户名</label>
                    <input
                      type="text"
                      id="username"
                      v-model="userForm.username"
                      required
                      class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label for="email" class="block text-sm font-medium text-gray-700">邮箱</label>
                    <input
                      type="email"
                      id="email"
                      v-model="userForm.email"
                      required
                      class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label for="organization" class="block text-sm font-medium text-gray-700">组织</label>
                    <input
                      type="text"
                      id="organization"
                      v-model="userForm.organization"
                      required
                      class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label for="role" class="block text-sm font-medium text-gray-700">角色</label>
                    <select
                      id="role"
                      v-model="userForm.role"
                      class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    >
                      <option value="user">普通用户</option>
                      <option value="admin">管理员</option>
                    </select>
                  </div>
                  <div class="flex items-center">
                    <input
                      id="is_active"
                      type="checkbox"
                      v-model="userForm.is_active"
                      class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <label for="is_active" class="ml-2 block text-sm text-gray-900">
                      激活账号
                    </label>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
            <button
              type="button"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
              @click="handleSubmit"
            >
              {{ showAddUserDialog ? '添加' : '保存' }}
            </button>
            <button
              type="button"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
              @click="handleCancel"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { formatDate } from '@/utils/format'
import type { User } from '@/types/auth'

// 状态
const users = ref<User[]>([
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    organization: '系统管理部',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    username: 'user1',
    email: 'user1@example.com',
    role: 'user',
    organization: '研发部',
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z'
  }
])

const searchQuery = ref('')
const showAddUserDialog = ref(false)
const showEditUserDialog = ref(false)
const userForm = ref<Partial<User>>({
  username: '',
  email: '',
  role: 'user',
  organization: '',
  is_active: true
})

// 计算属性
const filteredUsers = computed(() => {
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(
    user =>
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query) ||
      user.organization.toLowerCase().includes(query)
  )
})

// 方法
const handleRefresh = async () => {
  // TODO: 从API获取用户列表
  console.log('Refresh users')
}

const handleSearch = () => {
  // 搜索已经通过计算属性实现
  console.log('Search users with query:', searchQuery.value)
}

const handleEdit = (user: User) => {
  userForm.value = { ...user }
  showEditUserDialog.value = true
}

const handleDelete = async (user: User) => {
  if (confirm(`确定要删除用户 ${user.username} 吗？`)) {
    // TODO: 调用API删除用户
    console.log('Delete user:', user)
    users.value = users.value.filter(u => u.id !== user.id)
  }
}

const handleSubmit = async () => {
  try {
    if (showAddUserDialog.value) {
      // TODO: 调用API添加用户
      console.log('Add user:', userForm.value)
      users.value.push({
        id: users.value.length + 1,
        ...userForm.value as User,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
    } else {
      // TODO: 调用API更新用户
      console.log('Update user:', userForm.value)
      const index = users.value.findIndex(u => u.id === userForm.value.id)
      if (index !== -1) {
        users.value[index] = {
          ...users.value[index],
          ...userForm.value,
          updated_at: new Date().toISOString()
        }
      }
    }
    handleCancel()
  } catch (error) {
    console.error('Failed to save user:', error)
  }
}

const handleCancel = () => {
  showAddUserDialog.value = false
  showEditUserDialog.value = false
  userForm.value = {
    username: '',
    email: '',
    role: 'user',
    organization: '',
    is_active: true
  }
}
</script>