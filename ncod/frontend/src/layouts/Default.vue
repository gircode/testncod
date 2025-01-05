<template>
  <el-container class="layout-container">
    <el-aside width="200px">
      <el-menu
        :router="true"
        :default-active="route.path"
        class="menu-vertical"
      >
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        
        <el-menu-item index="/devices">
          <el-icon><Connection /></el-icon>
          <span>设备管理</span>
        </el-menu-item>
        
        <template v-if="userStore.isAdmin">
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          
          <el-menu-item index="/organizations">
            <el-icon><OfficeBuilding /></el-icon>
            <span>组织管理</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>{{ route.meta.title || 'NCOD系统' }}</h2>
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              {{ userStore.currentUser?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import {
  Monitor,
  Connection,
  User,
  OfficeBuilding,
  ArrowDown
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      userStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.menu-vertical {
  height: 100%;
  border-right: none;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  padding: 0 20px;
}

.header-content {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 