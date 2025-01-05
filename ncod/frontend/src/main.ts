import './styles/index.less'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

import AppComponent from './App.vue'
import router from './router'
import permission from './directives/permission'
import Message from './utils/message'

// 导入全局样式
import './assets/main.css'

const app = createApp(AppComponent)

// 注册 Pinia
app.use(createPinia())

// 注册路由
app.use(router)

// 注册权限指令
app.directive('permission', permission)

// 注册全局属性
app.config.globalProperties.$message = Message

// 错误处理
app.config.errorHandler = (err: unknown, _instance: any, info: string) => {
  console.error('Global error:', err)
  console.error('Error info:', info)
  // 显示错误提示
  const message = app.config.globalProperties.$message
  if (message) {
    message.error('系统错误，请稍后重试')
  }
}

// 注册 Ant Design Vue
app.use(Antd)

// 挂载应用
app.mount('#app') 