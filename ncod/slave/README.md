# NCOD从服务器

NCOD从服务器是一个基于FastAPI的监控服务,用于收集和管理系统性能指标。

## 功能特性

- 系统监控
  - CPU使用率监控
  - 内存使用情况监控
  - 磁盘使用情况监控
  - 网络状态监控
  
- 健康检查
  - 系统健康状态检查
  - 数据库连接检查
  - 系统概况统计
  
- 告警管理
  - 阈值告警
  - 告警通知
  - 告警处理
  
- 数据管理
  - 指标数据存储
  - 历史数据清理
  - 数据查询和统计

## 技术栈

- FastAPI: Web框架
- SQLAlchemy: ORM框架
- PostgreSQL: 数据库
- Redis: 缓存
- Alembic: 数据库迁移
- pytest: 测试框架
- Docker: 容器化部署

## 快速开始

1. 克隆项目:

```bash
git clone https://github.com/your-repo/ncod.git
cd ncod/slave
```

**2. 安装依赖:**

```bash
pip install -r requirements.txt
```

**3. 配置环境变量:**

```bash
cp .env.example .env
# 编辑.env文件,配置数据库等信息
```

**4. 初始化数据库:**

```bash
alembic upgrade head
```

**5. 启动服务:**

```bash
uvicorn app.main:app --reload
```

## Docker部署

**使用Docker Compose启动服务:**

```bash
docker-compose up -d
```

## API文档

启动服务后访问: <http://localhost:8000/docs>

**主要接口:**

- GET /api/v1/monitor/metrics - 获取监控指标
- GET /api/v1/monitor/alerts - 获取告警信息
- GET /api/v1/monitor/health/check - 健康检查
- GET /api/v1/monitor/health/summary - 系统概况

## 测试

**运行测试:**

```bash
pytest
```

## 配置说明

**主要配置项(app/core/config.py):**

- MONITOR_INTERVAL: 监控间隔(秒)
- CPU_THRESHOLD: CPU告警阈值(%)
- MEMORY_THRESHOLD: 内存告警阈值(%)
- DISK_THRESHOLD: 磁盘告警阈值(%)
- DATA_RETENTION_DAYS: 数据保留天数

**项目结构:**

app/
├── api/            # API路由
├── core/           # 核心配置
├── db/             # 数据库
├── models/         # 数据模型
├── services/       # 业务服务
└── tests/          # 测试用例

## 开发指南

**1. 代码规范**

- 遵循PEP 8规范
- 使用类型注解
- 编写详细的文档字符串

**2. 提交规范**

- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 其他更新

**许可证:**

MIT License
