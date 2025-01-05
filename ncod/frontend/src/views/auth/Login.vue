<template>
  <div class="login-container">
    <img src="@/assets/images/logo.svg" alt="Logo" class="logo">
    <h1 class="system-title">设备管理系统</h1>
    
    <div class="login-box">
      <h2 class="login-title">账号密码登录</h2>
      
      <div class="form-item">
        <span class="required">*</span>
        <label>用户名</label>
        <input type="text" 
               v-model="formState.username" 
               placeholder="请输入用户名"
               class="input-field">
      </div>
      
      <div class="form-item">
        <span class="required">*</span>
        <label>密码</label>
        <div class="password-input">
          <input :type="showPassword ? 'text' : 'password'" 
                 v-model="formState.password" 
                 placeholder="请输入密码"
                 class="input-field">
          <i class="password-eye" 
             :class="{ 'show': showPassword }"
             @click="togglePassword"></i>
        </div>
      </div>
      
      <div class="remember-forgot">
        <label class="remember">
          <input type="checkbox" v-model="formState.remember">
          记住密码
        </label>
        <a href="#" class="forgot-link">忘记密码?</a>
      </div>
      
      <button class="login-button" 
              @click="handleFinish(formState)"
              :disabled="loading">
        {{ loading ? '登录中...' : '登 录' }}
      </button>
      
      <div class="register-link">
        还没有账号? <a href="#" @click="goToRegister">立即注册</a>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { request } from '@/utils/request'
import type { LoginResponseData, LoginParams } from '@/types/api'

interface FormState extends LoginParams {
  remember: boolean
}

const router = useRouter()
const loading = ref(false)
const showPassword = ref(false)

const formState = reactive<FormState>({
  username: '',
  password: '',
  remember: false
})

// 从本地存储加载保存的账号密码
onMounted(() => {
  const savedCredentials = localStorage.getItem('credentials')
  if (savedCredentials) {
    try {
      const decoded = JSON.parse(atob(savedCredentials))
      formState.username = decoded.username
      formState.password = decoded.password
      formState.remember = decoded.remember
    } catch (error) {
      console.error('读取保存的账号密码失败:', error)
      localStorage.removeItem('credentials')
    }
  }
})

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const handleFinish = async (values: FormState) => {
  if (!values.username || !values.password) {
    message.error('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    const { token, refreshToken, user } = await request<LoginResponseData['data']>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        username: values.username,
        password: values.password
      })
    })

    // 保存token和用户信息
    localStorage.setItem('token', token)
    localStorage.setItem('refreshToken', refreshToken)
    localStorage.setItem('user', JSON.stringify(user))
    
    // 如果选择记住密码，使用加密存储账号密码
    if (values.remember) {
      const credentials = btoa(JSON.stringify({
        username: values.username,
        password: values.password,
        remember: true
      }))
      localStorage.setItem('credentials', credentials)
    } else {
      localStorage.removeItem('credentials')
    }
    
    message.success('登录成功')
    await router.push('/')
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push('/auth/register')
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e90ff 0%, #4169e1 100%);
  padding: 20px;
}

.system-title {
  color: white;
  font-size: 28px;
  margin: 20px 0;
}

.login-box {
  background: white;
  border-radius: 8px;
  padding: 30px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.login-title {
  text-align: center;
  font-size: 24px;
  margin-bottom: 30px;
  color: #333;
}

.form-item {
  margin-bottom: 20px;
  
  label {
    display: block;
    margin-bottom: 8px;
    color: #606266;
  }
}

.input-field {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: #409eff;
    outline: none;
  }
}

.password-input {
  position: relative;
  display: flex;
  align-items: center;
  
  .password-eye {
    position: absolute;
    right: 10px;
    width: 20px;
    height: 20px;
    cursor: pointer;
    background: url('@/assets/images/eye-off.svg') no-repeat center;
    
    &.show {
      background-image: url('@/assets/images/eye-on.svg');
    }
  }
}

.required {
  color: #f56c6c;
  margin-right: 4px;
}

.login-button {
  width: 100%;
  padding: 12px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
  transition: background-color 0.3s;

  &:hover {
    background: #66b1ff;
  }

  &:disabled {
    background: #a0cfff;
    cursor: not-allowed;
  }
}

.remember-forgot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 15px 0;
  
  .remember {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #606266;
    cursor: pointer;
    
    input[type="checkbox"] {
      margin: 0;
    }
  }
  
  .forgot-link {
    color: #409eff;
    text-decoration: none;
    font-size: 14px;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.register-link {
  text-align: center;
  margin-top: 20px;
  color: #606266;
  font-size: 14px;
  
  a {
    color: #409eff;
    text-decoration: none;
    margin-left: 4px;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.logo {
  width: 200px;
  height: 60px;
  margin-bottom: 20px;
}
</style>
