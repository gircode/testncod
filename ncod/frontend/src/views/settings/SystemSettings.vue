<template>
  <div class="system-settings">
    <a-card title="系统设置" :bordered="false">
      <a-form
        :model="formState"
        :rules="rules"
        layout="vertical"
        @finish="onFinish"
      >
        <a-form-item label="系统名称" name="systemName">
          <a-input v-model:value="formState.systemName" />
        </a-form-item>
        
        <a-form-item label="会话超时时间(分钟)" name="sessionTimeout">
          <a-input-number
            v-model:value="formState.sessionTimeout"
            :min="5"
            :max="1440"
          />
        </a-form-item>
        
        <a-form-item label="日志保留天数" name="logRetentionDays">
          <a-input-number
            v-model:value="formState.logRetentionDays"
            :min="7"
            :max="365"
          />
        </a-form-item>
        
        <a-form-item label="允许同时登录" name="allowMultipleLogin">
          <a-switch v-model:checked="formState.allowMultipleLogin" />
        </a-form-item>
        
        <a-form-item label="启用MAC地址验证" name="enableMacAuth">
          <a-switch v-model:checked="formState.enableMacAuth" />
        </a-form-item>
        
        <a-form-item>
          <a-button type="primary" html-type="submit">保存设置</a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from 'vue'
import { message } from 'ant-design-vue'
import type { Rule } from 'ant-design-vue/es/form'

interface FormState {
  systemName: string
  sessionTimeout: number
  logRetentionDays: number
  allowMultipleLogin: boolean
  enableMacAuth: boolean
}

export default defineComponent({
  name: 'SystemSettings',
  setup() {
    const formState = reactive<FormState>({
      systemName: 'USB设备管理系统',
      sessionTimeout: 30,
      logRetentionDays: 30,
      allowMultipleLogin: false,
      enableMacAuth: true
    })

    const rules: Record<string, Rule[]> = {
      systemName: [
        { required: true, message: '请输入系统名称' },
        { max: 50, message: '系统名称不能超过50个字符' }
      ],
      sessionTimeout: [
        { required: true, message: '请输入会话超时时间' },
        { type: 'number', min: 5, max: 1440, message: '超时时间必须在5-1440分钟之间' }
      ],
      logRetentionDays: [
        { required: true, message: '请输入日志保留天数' },
        { type: 'number', min: 7, max: 365, message: '保留天数必须在7-365天之间' }
      ]
    }

    const onFinish = (values: FormState) => {
      console.log('表单数据:', values)
      message.success('设置已保存')
    }

    return {
      formState,
      rules,
      onFinish
    }
  }
})
</script>

<style scoped>
.system-settings {
  padding: 24px;
  background: #f0f2f5;
}
</style> 