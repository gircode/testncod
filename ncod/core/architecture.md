# 核心架构设计

## 1. 主从服务器架构

master/
  ├── api/          # RESTful API接口
  ├── auth/         # 认证与授权
  ├── models/       # 数据模型
  └── services/     # 业务逻辑

slave/
  ├── device/       # 设备管理
  ├── monitor/      # 监控上报
  └── sync/         # 数据同步

## 2. 数据流设计

- 设备数据流: Slave -> Master -> Cache -> Database
- 用户操作流: Frontend -> API -> Service -> Database
- 实时监控流: Slave -> WebSocket -> Frontend

## 3. 安全架构

- JWT + MAC地址双重认证
- HTTPS加密传输
- RBAC权限控制
- 操作审计日志
