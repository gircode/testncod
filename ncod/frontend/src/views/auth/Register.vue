<!-- 注册页面 -->
<template>
  <div class="register-container">
    <div class="register-content">
      <h1 class="register-title">注册新账号</h1>
      <div class="register-form">
        <a-form
          ref="formRef"
          :model="formState"
          :rules="rules"
          @submit.prevent="handleSubmit"
        >
          <a-form-item name="username">
            <a-input
              v-model:value="formState.username"
              placeholder="请输入用户名"
              size="large"
            >
              <template #prefix>
                <UserOutlined />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item name="email">
            <a-input
              v-model:value="formState.email"
              placeholder="请输入邮箱"
              size="large"
            >
              <template #prefix>
                <MailOutlined />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item name="password">
            <a-input-password
              v-model:value="formState.password"
              placeholder="请输入密码"
              size="large"
            >
              <template #prefix>
                <LockOutlined />
              </template>
            </a-input-password>
          </a-form-item>

          <a-form-item name="confirmPassword">
            <a-input-password
              v-model:value="formState.confirmPassword"
              placeholder="请确认密码"
              size="large"
            >
              <template #prefix>
                <LockOutlined />
              </template>
            </a-input-password>
          </a-form-item>

          <div class="form-footer">
            <router-link to="/auth/login" class="login-link">返回登录</router-link>
          </div>

          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            class="register-button"
            size="large"
            block
          >
            注册
          </a-button>
        </a-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import UserOutlined from '@ant-design/icons-vue/es/icons/UserOutlined'
import LockOutlined from '@ant-design/icons-vue/es/icons/LockOutlined'
import MailOutlined from '@ant-design/icons-vue/es/icons/MailOutlined'
import { useAuthStore } from '@/store/auth'
import type { AuthStore } from '@/store/auth'
import type { RegisterForm } from '@/types/user'

const router = useRouter()
const store = useAuthStore() as AuthStore
const loading = ref(false)
const formRef = ref()

const formState = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  organization: undefined
})

const validateConfirmPassword = async (_rule: any, value: string) => {
  if (!value) {
    return Promise.reject('请确认密码')
  }
  if (value !== formState.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, message: '用户名至少4个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  try {
    loading.value = true
    await formRef.value.validateFields()
    const success = await store.register(formState)
    
    if (success) {
      message.success('注册成功')
      router.push('/auth/login')
    } else {
      message.error('注册失败，请重试')
    }
  } catch (error: any) {
    console.error('Registration error:', error)
    message.error(error?.message || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="less" scoped>
.register-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2d3a4b;
  overflow: auto;
}

.register-content {
  width: 90%;
  max-width: 360px;
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box;

  @media screen and (min-width: 1920px) {
    max-width: 400px;
  }

  @media screen and (max-width: 768px) {
    max-width: 320px;
  }
}

.register-title {
  text-align: center;
  color: #fff;
  font-size: clamp(20px, 4vw, 26px);
  margin-bottom: clamp(20px, 4vh, 40px);
  font-weight: 500;
}

.register-form {
  :deep(.ant-input-affix-wrapper) {
    background: rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    height: clamp(40px, 5vh, 47px);
    padding: 0 15px;

    input {
      background: transparent !important;
      color: #fff !important;
      font-size: 14px;
      height: 100%;

      &::placeholder {
        color: rgba(255, 255, 255, 0.7);
      }
    }

    .anticon {
      color: rgba(255, 255, 255, 0.7);
      font-size: 16px;
    }

    &:hover,
    &:focus,
    &-focused {
      border-color: #1890ff !important;
      background: rgba(0, 0, 0, 0.2) !important;
      box-shadow: none !important;
    }
  }

  :deep(.ant-form-item-explain-error) {
    color: #ff4d4f;
    font-size: 13px;
  }

  :deep(.ant-form-item) {
    margin-bottom: clamp(15px, 2vh, 20px);
  }
}

.form-footer {
  text-align: right;
  margin-bottom: clamp(15px, 2vh, 20px);

  .login-link {
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
    text-decoration: none;
    transition: color 0.3s ease;

    &:hover {
      color: #fff;
    }
  }
}

.register-button {
  height: clamp(40px, 5vh, 47px);
  font-size: 16px;
  background: #1890ff;
  border: none;
  width: 100%;
  transition: all 0.3s ease;

  &:hover {
    background: #40a9ff;
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
}
</style>