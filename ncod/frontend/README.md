# NCOD Frontend

基于Vue 3 + TypeScript + Vite的设备管理系统前端。

## 开发环境

- Node.js >= 16.0.0
- npm >= 8.0.0

## 项目设置

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码格式化
npm run format

# 代码检查
npm run lint
```

## 项目结构

```tree
src/
├── api/          # API请求
├── components/   # 通用组件
├── layouts/      # 布局组件
├── router/       # 路由配置
├── store/        # 状态管理
├── types/        # TypeScript类型定义
├── utils/        # 工具函数
└── views/        # 页面组件
```

## 环境变量

- `VITE_API_URL`: API服务器地址
- `VITE_WS_URL`: WebSocket服务器地址

## 开发规范

- 使用TypeScript编写代码
- 遵循ESLint和Prettier配置的代码风格
- 组件使用Composition API和`<script setup>`语法
- API请求统一在api目录下管理
- 使用Pinia进行状态管理
