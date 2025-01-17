# NCOD 项目结构说明

## 目录结构

```
ncod/
├── api/                    # API 接口层
│   └── v1/                # API 版本 1
│       └── endpoints/     # API 端点定义
├── core/                  # 核心功能模块
│   ├── auth.py           # 认证相关功能
│   ├── config.py         # 配置管理
│   ├── db.py            # 数据库管理
│   ├── device.py        # 设备管理核心
│   ├── monitor.py       # 系统监控
│   ├── security.py      # 安全相关功能
│   └── websocket.py     # WebSocket 管理
├── models/               # 数据库模型
│   ├── auth.py          # 认证相关模型
│   ├── device.py        # 设备相关模型
│   └── user.py          # 用户相关模型
├── schemas/             # 数据验证模式
│   ├── auth.py         # 认证相关模式
│   └── device.py       # 设备相关模式
├── utils/              # 工具函数
│   └── logger.py      # 日志工具
├── master/            # 主节点应用
│   └── app/          # 主节点应用代码
│       └── services/ # 主节点服务
├── slave/            # 从节点应用
│   └── app/         # 从节点应用代码
│       └── services/ # 从节点服务
├── tests/           # 测试代码
├── docs/           # 项目文档
├── main.py         # 主程序入口
└── __init__.py     # 包初始化文件

## 主要模块说明

### API 层 (api/)
- 处理所有的 HTTP/WebSocket 请求
- 实现 RESTful API 接口
- 处理请求验证和响应格式化

### 核心层 (core/)
- 实现核心业务逻辑
- 提供基础设施服务
- 管理系统配置和安全

### 数据层 (models/ & schemas/)
- 定义数据库模型
- 实现数据验证和序列化
- 管理数据关系和完整性

### 主从节点 (master/ & slave/)
- 实现分布式系统架构
- 处理节点间通信和同步
- 管理设备和任务分配

### 工具层 (utils/)
- 提供通用工具函数
- 实现日志和监控
- 提供辅助功能

## 开发规范

1. 代码组织
   - 遵循单一职责原则
   - 保持模块间低耦合
   - 使用依赖注入管理服务

2. 命名规范
   - 使用小写字母和下划线命名文件
   - 使用驼峰命名类
   - 使用下划线命名函数和变量

3. 文档规范
   - 所有模块、类和函数都应有文档字符串
   - 复杂逻辑应有注释说明
   - 保持文档的及时更新

4. 测试规范
   - 编写单元测试和集成测试
   - 保持测试覆盖率
   - 实现自动化测试 