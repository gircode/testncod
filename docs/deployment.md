# NCOD 部署指南

本文档详细说明了如何在生产环境中部署 NCOD 系统。

## 系统要求

- Python 3.12+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (用于前端构建)
- VirtualHere Server/Client

## 安装步骤

### 1. 准备环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果需要开发工具
```

### 2. 配置数据库

```bash
# 创建数据库
createdb ncod

# 初始化数据库
python -m ncod.cli db init
python -m ncod.cli db migrate
python -m ncod.cli db upgrade
```

### 3. 配置环境变量

创建 `.env` 文件并设置以下变量：

```env
# 基础配置
DEBUG=false
WORKER_PROCESSES=4

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=ncod

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT配置
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# VirtualHere配置
VH_SERVER_HOST=localhost
VH_SERVER_PORT=7575
```

### 4. 构建前端

```bash
# 安装前端依赖
cd ncod/frontend
npm install

# 构建前端
npm run build
```

### 5. 配置 Nginx

创建 Nginx 配置文件：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

### 6. 配置 Systemd 服务

创建主服务器服务文件 `/etc/systemd/system/ncod-master.service`：

```ini
[Unit]
Description=NCOD Master Server
After=network.target

[Service]
User=ncod
Group=ncod
WorkingDirectory=/opt/ncod
Environment="PATH=/opt/ncod/venv/bin"
ExecStart=/opt/ncod/venv/bin/python -m ncod.cli server start

[Install]
WantedBy=multi-user.target
```

创建从服务器服务文件 `/etc/systemd/system/ncod-slave.service`：

```ini
[Unit]
Description=NCOD Slave Server
After=network.target

[Service]
User=ncod
Group=ncod
WorkingDirectory=/opt/ncod
Environment="PATH=/opt/ncod/venv/bin"
ExecStart=/opt/ncod/venv/bin/python -m ncod.cli slave start

[Install]
WantedBy=multi-user.target
```

### 7. 启动服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ncod-master
sudo systemctl start ncod-slave

# 设置开机自启
sudo systemctl enable ncod-master
sudo systemctl enable ncod-slave
```

### 8. 配置监控

#### Prometheus

创建 Prometheus 配置文件 `/etc/prometheus/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ncod'
    static_configs:
      - targets: ['localhost:8000']
```

#### Grafana

1. 安装 Grafana
2. 添加 Prometheus 数据源
3. 导入监控面板

## 安全配置

### 1. 防火墙配置

```bash
# 开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 7575/tcp  # VirtualHere
```

### 2. SSL 配置

使用 Let's Encrypt 配置 SSL：

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your_domain.com
```

### 3. 数据备份

创建备份脚本 `/opt/ncod/scripts/backup.sh`：

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=/var/backups/ncod

# 备份数据库
pg_dump ncod > $BACKUP_DIR/ncod_$DATE.sql

# 备份配置文件
cp /opt/ncod/.env $BACKUP_DIR/env_$DATE
cp /opt/ncod/config/* $BACKUP_DIR/config_$DATE/

# 压缩备份
tar -czf $BACKUP_DIR/ncod_backup_$DATE.tar.gz $BACKUP_DIR/ncod_$DATE.sql $BACKUP_DIR/env_$DATE $BACKUP_DIR/config_$DATE/

# 删除30天前的备份
find $BACKUP_DIR -name "ncod_backup_*.tar.gz" -mtime +30 -delete
```

添加到 crontab：

```bash
0 2 * * * /opt/ncod/scripts/backup.sh
```

## 故障排除

### 1. 日志位置

- 主服务器日志: `/var/log/ncod/master.log`
- 从服务器日志: `/var/log/ncod/slave.log`
- Nginx 日志: `/var/log/nginx/ncod.log`
- VirtualHere 日志: `/var/log/virtualhere/server.log`

### 2. 常见问题

1. 数据库连接失败
   - 检查数据库凭据
   - 检查数据库服务状态
   - 检查防火墙规则

2. WebSocket 连接失败
   - 检查 Nginx 配置
   - 检查防火墙规则
   - 检查 SSL 配置

3. 设备连接失败
   - 检查 VirtualHere 服务状态
   - 检查设备权限
   - 检查 USB 驱动

### 3. 性能优化

1. 数据库优化
   - 添加适当的索引
   - 配置连接池
   - 定期维护

2. 缓存优化
   - 配置 Redis 持久化
   - 调整缓存过期时间
   - 监控缓存命中率

3. 应用优化
   - 调整工作进程数
   - 配置异步任务队列
   - 启用压缩

## 更新流程

1. 备份数据

```bash
./scripts/backup.sh
```

2. 更新代码

```bash
git pull origin main
```

3. 更新依赖

```bash
pip install -r requirements.txt --upgrade
```

4. 数据库迁移

```bash
python -m ncod.cli db upgrade
```

5. 重启服务

```bash
sudo systemctl restart ncod-master
sudo systemctl restart ncod-slave
```

## 监控指标

### 1. 系统指标

- CPU 使用率
- 内存使用率
- 磁盘使用率
- 网络流量

### 2. 应用指标

- API 请求率
- 响应时间
- 错误率
- 活跃连接数

### 3. 设备指标

- 设备连接数
- 设备状态分布
- 设备错误率
- 带宽使用率

## 安全检查清单

- [ ] 更改默认密码
- [ ] 配置防火墙规则
- [ ] 启用 SSL/TLS
- [ ] 配置数据库访问权限
- [ ] 设置文件权限
- [ ] 启用审计日志
- [ ] 配置备份策略
- [ ] 更新系统补丁
- [ ] 禁用不必要的服务
- [ ] 配置监控告警
