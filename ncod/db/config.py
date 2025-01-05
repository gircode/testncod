"""数据库配置模块"""

import os
from typing import Dict, Any


def read_password() -> str:
    """从密钥文件读取数据库密码"""
    password_file = os.path.join(
        os.path.dirname(__file__), "../../keys/db_password.key"
    )
    try:
        with open(password_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return os.getenv("POSTGRES_PASSWORD", "postgres")


DB_CONFIG: Dict[str, Any] = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "ncod"),
    "user": os.getenv("DB_USER", "ncod_user"),
    "password": os.getenv("DB_PASSWORD", read_password()),
}
