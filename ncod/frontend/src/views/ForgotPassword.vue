<template>
  <div class="forgot-password-container">
    <div class="forgot-password-box">
      <div class="forgot-password-header">
        <img src="@/assets/logo.png" alt="Logo" class="logo" />
        <h1>找回密码</h1>
      </div>
      <a-card class="forgot-password-card">
        <a-steps :current="currentStep" class="steps">
          <a-step title="验证身份" />
          <a-step title="重置密码" />
          <a-step title="完成" />
        </a-steps>

        <!-- 步骤1：验证身份 -->
        <div v-if="currentStep === 0">
          <a-form
            :model="verifyForm"
            @finish="handleVerifySubmit"
            layout="vertical"
          >
            <a-form-item
              label="用户名"
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
            >
              <a-input 
                v-model:value="verifyForm.username"
                prefix="user"
                placeholder="请输入用户名"
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
                v-model:value="verifyForm.email"
                prefix="mail"
                placeholder="请输入邮箱"
                size="large"
              />
            </a-form-item>

            <a-form-item
              label="验证码"
              name="verifyCode"
              :rules="[{ required: true, message: '请输入验证码' }]"
            >
              <div class="verify-code-container">
                <a-input 
                  v-model:value="verifyForm.verifyCode"
                  placeholder="请输入验证码"
                  size="large"
                />
                <a-button 
                  :disabled="!!countdown || loading"
                  @click="handleSendCode"
                  size="large"
                >
                  {{ countdown ? `${countdown}秒后重试` : '获取验证码' }}
                </a-button>
              </div>
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                :loading="loading"
                size="large"
                block
              >
                下一步
              </a-button>
            </a-form-item>
          </a-form>
        </div>

        <!-- 步骤2：重置密码 -->
        <div v-if="currentStep === 1">
          <a-form
            :model="resetForm"
            @finish="handleResetSubmit"
            layout="vertical"
          >
            <a-form-item
              label="新密码"
              name="newPassword"
              :rules="[
                { required: true, message: '请输入新密码' },
                { min: 6, message: '密码至少6个字符' },
                { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{6,}$/, message: '密码必须包含大小写字母和数字' }
              ]"
            >
              <a-input-password 
                v-model:value="resetForm.newPassword"
                prefix="lock"
                placeholder="请输入新密码"
                size="large"
              />
            </a-form-item>

            <a-form-item
              label="确认新密码"
              name="confirmPassword"
              :rules="[
                { required: true, message: '请确认新密码' },
                { validator: validateConfirmPassword }
              ]"
            >
              <a-input-password 
                v-model:value="resetForm.confirmPassword"
                prefix="lock"
                placeholder="请确认新密码"
                size="large"
              />
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                :loading="loading"
                size="large"
                block
              >
                重置密码
              </a-button>
            </a-form-item>
          </a-form>
        </div>

        <!-- 步骤3：完成 -->
        <div v-if="currentStep === 2" class="success-step">
          <a-result
            status="success"
            title="密码重置成功！"
            sub-title="您的密码已经重置成功，请使用新密码登录。"
          >
            <template #extra>
              <a-button
                type="primary"
                @click="handleBackToLogin"
                size="large"
              >
                返回登录
              </a-button>
            </template>
          </a-result>
        </div>

        <div class="back-to-login">
          <a @click="handleBackToLogin">返回登录</a>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { useAuthStore } from '@/store/auth';

interface VerifyForm {
  username: string;
  email: string;
  verifyCode: string;
}

interface ResetForm {
  newPassword: string;
  confirmPassword: string;
}

export default defineComponent({
  name: 'ForgotPassword',
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const loading = ref(false);
    const currentStep = ref(0);
    const countdown = ref(0);
    let countdownTimer: number;

    const verifyForm = reactive<VerifyForm>({
      username: '',
      email: '',
      verifyCode: ''
    });

    const resetForm = reactive<ResetForm>({
      newPassword: '',
      confirmPassword: ''
    });

    const startCountdown = () => {
      countdown.value = 60;
      countdownTimer = window.setInterval(() => {
        if (countdown.value > 0) {
          countdown.value--;
        } else {
          clearInterval(countdownTimer);
        }
      }, 1000);
    };

    const handleSendCode = async () => {
      if (!verifyForm.email) {
        message.error('请先输入邮箱');
        return;
      }

      try {
        loading.value = true;
        const success = await authStore.sendVerifyCode(verifyForm.email);
        if (success) {
          message.success('验证码已发送到您的邮箱');
          startCountdown();
        }
      } catch (error) {
        message.error('发送验证码失败：' + (error as Error).message);
      } finally {
        loading.value = false;
      }
    };

    const handleVerifySubmit = async (values: VerifyForm) => {
      try {
        loading.value = true;
        const success = await authStore.verifyResetCode({
          username: values.username,
          email: values.email,
          code: values.verifyCode
        });
        
        if (success) {
          currentStep.value = 1;
        }
      } catch (error) {
        message.error('验证失败：' + (error as Error).message);
      } finally {
        loading.value = false;
      }
    };

    const validateConfirmPassword = async (_rule: any, value: string) => {
      if (value !== resetForm.newPassword) {
        throw new Error('两次输入的密码不一致');
      }
    };

    const handleResetSubmit = async (values: ResetForm) => {
      try {
        loading.value = true;
        const success = await authStore.resetPassword({
          username: verifyForm.username,
          code: verifyForm.verifyCode,
          newPassword: values.newPassword
        });
        
        if (success) {
          currentStep.value = 2;
        }
      } catch (error) {
        message.error('重置密码失败：' + (error as Error).message);
      } finally {
        loading.value = false;
      }
    };

    const handleBackToLogin = () => {
      router.push('/login');
    };

    return {
      currentStep,
      loading,
      countdown,
      verifyForm,
      resetForm,
      handleSendCode,
      handleVerifySubmit,
      validateConfirmPassword,
      handleResetSubmit,
      handleBackToLogin
    };
  }
});
</script>

<style lang="less" scoped>
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  padding: 20px;

  .forgot-password-box {
    width: 100%;
    max-width: 480px;
  }

  .forgot-password-header {
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

  .forgot-password-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);

    :deep(.ant-card-body) {
      padding: 24px;
    }
  }

  .steps {
    margin-bottom: 32px;
  }

  .verify-code-container {
    display: flex;
    gap: 12px;

    .ant-input {
      flex: 1;
    }

    .ant-btn {
      min-width: 120px;
    }
  }

  .success-step {
    padding: 32px 0;
  }

  .back-to-login {
    text-align: center;
    margin-top: 16px;
  }
}
</style> 