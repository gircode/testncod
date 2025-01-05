<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <img src="@/assets/logo.png" alt="Logo" class="logo" />
        <h1>用户注册</h1>
      </div>
      <a-card class="register-card">
        <a-form
          :model="formState"
          @finish="handleSubmit"
          layout="vertical"
        >
          <a-form-item
            label="用户名"
            name="username"
            :rules="[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
            ]"
          >
            <a-input 
              v-model:value="formState.username"
              prefix="user"
              placeholder="请输入用户名"
              size="large"
            />
          </a-form-item>

          <a-form-item
            label="密码"
            name="password"
            :rules="[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
              { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{6,}$/, message: '密码必须包含大小写字母和数字' }
            ]"
          >
            <a-input-password 
              v-model:value="formState.password"
              prefix="lock"
              placeholder="请输入密码"
              size="large"
            />
          </a-form-item>

          <a-form-item
            label="确认密码"
            name="confirmPassword"
            :rules="[
              { required: true, message: '请确认密码' },
              { validator: validateConfirmPassword }
            ]"
          >
            <a-input-password 
              v-model:value="formState.confirmPassword"
              prefix="lock"
              placeholder="请确认密码"
              size="large"
            />
          </a-form-item>

          <a-form-item
            label="邮箱"
            name="email"
            :rules="[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]"
          >
            <a-input 
              v-model:value="formState.email"
              prefix="mail"
              placeholder="请输入邮箱"
              size="large"
            />
          </a-form-item>

          <a-form-item
            label="手机号"
            name="phone"
            :rules="[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }
            ]"
          >
            <a-input 
              v-model:value="formState.phone"
              prefix="phone"
              placeholder="请输入手机号"
              size="large"
            />
          </a-form-item>

          <a-form-item
            name="captcha"
            label="验证码"
            :rules="[{ required: true, message: '请输入验证码' }]"
          >
            <div class="captcha-container">
              <a-input 
                v-model:value="formState.captcha"
                placeholder="请输入验证码"
                size="large"
              />
              <img 
                :src="captchaUrl" 
                alt="验证码"
                class="captcha-img"
                @click="refreshCaptcha"
              />
            </div>
          </a-form-item>

          <a-form-item>
            <a-checkbox 
              v-model:checked="formState.agreement"
              :rules="[{ required: true, message: '请阅读并同意用户协议' }]"
            >
              我已阅读并同意
              <a @click="showAgreement">《用户协议》</a>
            </a-checkbox>
          </a-form-item>

          <a-form-item>
            <a-button
              type="primary"
              html-type="submit"
              :loading="loading"
              size="large"
              block
            >
              注册
            </a-button>
          </a-form-item>

          <a-form-item>
            <div class="login-link">
              已有账号？
              <a @click="handleLogin">立即登录</a>
            </div>
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <a-modal
      v-model:visible="agreementVisible"
      title="用户协议"
      width="600px"
      @ok="handleAgreementOk"
    >
      <div class="agreement-content">
        <h3>用户协议</h3>
        <p>欢迎使用我们的设备管理系统！</p>
        <p>1. 服务说明</p>
        <p>本系统提供设备管理、监控和控制等服务。</p>
        <p>2. 用户责任</p>
        <p>用户应妥善保管账号和密码，对账号下的所有行为负责。</p>
        <p>3. 隐私保护</p>
        <p>我们会严格保护用户的个人信息和数据安全。</p>
        <p>4. 服务变更</p>
        <p>我们保留随时修改或中断服务的权利。</p>
      </div>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { useAuthStore } from '@/store/auth';

interface FormState {
  username: string;
  password: string;
  confirmPassword: string;
  email: string;
  phone: string;
  captcha: string;
  agreement: boolean;
}

export default defineComponent({
  name: 'Register',
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const loading = ref(false);
    const captchaUrl = ref('/api/auth/captcha');
    const agreementVisible = ref(false);

    const formState = reactive<FormState>({
      username: '',
      password: '',
      confirmPassword: '',
      email: '',
      phone: '',
      captcha: '',
      agreement: false
    });

    const validateConfirmPassword = async (_rule: any, value: string) => {
      if (value !== formState.password) {
        throw new Error('两次输入的密码不一致');
      }
    };

    const handleSubmit = async (values: FormState) => {
      if (!values.agreement) {
        message.error('请阅读并同意用户协议');
        return;
      }

      try {
        loading.value = true;
        const success = await authStore.register({
          username: values.username,
          password: values.password,
          email: values.email,
          phone: values.phone,
          captcha: values.captcha
        });
        
        if (success) {
          message.success('注册成功，请登录');
          router.push('/login');
        }
      } catch (error) {
        message.error('注册失败：' + (error as Error).message);
        refreshCaptcha();
      } finally {
        loading.value = false;
      }
    };

    const refreshCaptcha = () => {
      captchaUrl.value = `/api/auth/captcha?t=${Date.now()}`;
    };

    const handleLogin = () => {
      router.push('/login');
    };

    const showAgreement = () => {
      agreementVisible.value = true;
    };

    const handleAgreementOk = () => {
      agreementVisible.value = false;
      formState.agreement = true;
    };

    return {
      formState,
      loading,
      captchaUrl,
      agreementVisible,
      handleSubmit,
      validateConfirmPassword,
      refreshCaptcha,
      handleLogin,
      showAgreement,
      handleAgreementOk
    };
  }
});
</script>

<style lang="less" scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  padding: 20px;

  .register-box {
    width: 100%;
    max-width: 480px;
  }

  .register-header {
    text-align: center;
    margin-bottom: 24px;

    .logo {
      width: 80px;
      height: 80px;
      margin-bottom: 16px;
    }

    h1 {
      color: #fff;
      font-size: 28px;
      font-weight: 600;
      margin: 0;
    }
  }

  .register-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);

    :deep(.ant-card-body) {
      padding: 24px;
    }
  }

  .captcha-container {
    display: flex;
    gap: 12px;

    .captcha-img {
      height: 40px;
      cursor: pointer;
    }
  }

  .login-link {
    text-align: center;
    margin-top: 16px;
  }
}

.agreement-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 0 16px;

  h3 {
    text-align: center;
    margin-bottom: 24px;
  }

  p {
    margin-bottom: 16px;
    line-height: 1.6;
  }
}
</style> 