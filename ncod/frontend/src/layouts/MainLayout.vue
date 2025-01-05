<template>
  <div class="main-layout">
    <header class="header">
      <div class="logo-container">
        <img src="@/assets/images/logo.svg" alt="Logo" class="logo">
        <h1>设备管理系统</h1>
      </div>
      <div class="user-info">
        <span>{{ userInfo.username }}</span>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </header>
    
    <div class="main-content">
      <nav class="sidebar">
        <router-link to="/monitoring" class="nav-item" active-class="active">
          监控面板
        </router-link>
      </nav>
      
      <main class="content">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const userInfo = ref({
  username: '',
  role: ''
})

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    userInfo.value = JSON.parse(userStr)
  }
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/auth/login')
}
</script>

<style lang="scss" scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  
  .logo-container {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .logo {
      width: 40px;
      height: 40px;
    }
    
    h1 {
      font-size: 20px;
      color: #333;
      margin: 0;
    }
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 15px;
    
    span {
      color: #666;
    }
    
    .logout-btn {
      padding: 6px 12px;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      background: transparent;
      color: #606266;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        color: #409eff;
        border-color: #c6e2ff;
        background-color: #ecf5ff;
      }
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  background: #f5f7fa;
}

.sidebar {
  width: 200px;
  background: #fff;
  padding: 20px 0;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
  
  .nav-item {
    display: block;
    padding: 12px 20px;
    color: #606266;
    text-decoration: none;
    transition: all 0.3s;
    
    &:hover {
      color: #409eff;
      background: #ecf5ff;
    }
    
    &.active {
      color: #409eff;
      background: #ecf5ff;
      border-right: 3px solid #409eff;
    }
  }
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>