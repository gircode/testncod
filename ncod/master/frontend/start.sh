#!/bin/bash

# 确保脚本在错误时退出
set -e

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

# 检查PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL is not installed"
    exit 1
fi

# 检查Redis
if ! command -v redis-cli &> /dev/null; then
    echo "Error: Redis is not installed"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 创建必要的目录
echo "Creating required directories..."
mkdir -p logs
mkdir -p static
mkdir -p templates/email
mkdir -p config

# 检查配置文件
if [ ! -f "config/config.json" ]; then
    echo "Creating default config file..."
    cp config/config.example.json config/config.json
    echo "Please update config/config.json with your settings"
    exit 1
fi

# 检查数据库连接
echo "Checking database connection..."
if ! psql -h localhost -U master_user -d master_server -c '\q' 2>/dev/null; then
    echo "Creating database..."
    psql -h localhost -U postgres -c "CREATE USER master_user WITH PASSWORD 'master_password';"
    psql -h localhost -U postgres -c "CREATE DATABASE master_server OWNER master_user;"
fi

# 检查Redis连接
echo "Checking Redis connection..."
if ! redis-cli ping >/dev/null 2>&1; then
    echo "Error: Redis is not running"
    exit 1
fi

# 运行数据库迁移
echo "Running database migrations..."
python -m alembic upgrade head

# 初始化数据库
echo "Initializing database..."
python scripts/init_db.py

# 启动应用
echo "Starting application..."
python run.py 