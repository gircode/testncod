"""
安全密钥配置模块
包含所有需要的密钥和敏感信息
"""

import os
import secrets
from pathlib import Path

# 基础目录
BASE_DIR = Path(__file__).parent.parent

# JWT密钥
JWT_SECRET_KEY = secrets.token_urlsafe(32)

# 数据库凭证
DB_CREDENTIALS = {
    "user": "ncod_user",
    "password": secrets.token_urlsafe(16),
    "host": "localhost",
    "port": 5432,
    "database": "ncod",
}

# Redis凭证
REDIS_CREDENTIALS = {
    "host": "localhost",
    "port": 6379,
    "password": secrets.token_urlsafe(16),
    "db": 0,
}

# SMTP凭证
SMTP_CREDENTIALS = {
    "host": "smtp.example.com",
    "port": 587,
    "user": "notifications@example.com",
    "password": secrets.token_urlsafe(16),
}

# Slack凭证
SLACK_CREDENTIALS = {"api_token": secrets.token_urlsafe(32), "channel": "monitoring"}


# 保存密钥到文件
def save_keys():
    """保存所有密钥到对应的文件"""
    # JWT密钥
    with open(BASE_DIR / "keys/jwt_secret.key", "w") as f:
        f.write(JWT_SECRET_KEY)

    # 数据库密钥
    with open(BASE_DIR / "keys/db_password.key", "w") as f:
        f.write(DB_CREDENTIALS["password"])

    # Redis密钥
    with open(BASE_DIR / "keys/redis_password.key", "w") as f:
        f.write(REDIS_CREDENTIALS["password"])

    # SMTP密钥
    with open(BASE_DIR / "keys/smtp_password.key", "w") as f:
        f.write(SMTP_CREDENTIALS["password"])

    # Slack密钥
    with open(BASE_DIR / "keys/slack_token.key", "w") as f:
        f.write(SLACK_CREDENTIALS["api_token"])


if __name__ == "__main__":
    save_keys()
