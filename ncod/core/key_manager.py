"""
密钥管理模块
"""

import os
import json
import secrets
from pathlib import Path
from typing import Dict


class KeyManager:
    """密钥管理器"""

    def __init__(self, keys_dir: str = "D:/code/python/keys"):
        self.keys_dir = Path(keys_dir)
        self.keys_file = self.keys_dir / "keys.json"
        self.keys: Dict[str, str] = {}
        self._init_keys_dir()
        self._load_keys()

    def _init_keys_dir(self) -> None:
        """初始化密钥目录"""
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        if not self.keys_file.exists():
            self._generate_all_keys()

    def _load_keys(self) -> None:
        """加载密钥"""
        if self.keys_file.exists():
            with open(self.keys_file, "r", encoding="utf-8") as f:
                self.keys = json.load(f)

    def _save_keys(self) -> None:
        """保存密钥"""
        with open(self.keys_file, "w", encoding="utf-8") as f:
            json.dump(self.keys, f, indent=4)

    def _generate_key(self, length: int = 64) -> str:
        """生成密钥"""
        return secrets.token_urlsafe(length)

    def _generate_all_keys(self) -> None:
        """生成所有密钥"""
        self.keys = {
            # 核心密钥
            "SECRET_KEY": self._generate_key(),
            "JWT_SECRET_KEY": self._generate_key(),
            # 数据库密钥
            "DB_PASSWORD": self._generate_key(32),
            "DB_MASTER_PASSWORD": self._generate_key(32),
            "DB_SLAVE_PASSWORD": self._generate_key(32),
            # Redis密钥
            "REDIS_PASSWORD": self._generate_key(32),
            "REDIS_MASTER_PASSWORD": self._generate_key(32),
            "REDIS_SLAVE_PASSWORD": self._generate_key(32),
            # 加密密钥
            "ENCRYPTION_KEY": self._generate_key(),
            "AES_KEY": self._generate_key(32),
            "RSA_PRIVATE_KEY": self._generate_key(),
            "RSA_PUBLIC_KEY": self._generate_key(),
            # API密钥
            "API_KEY": self._generate_key(),
            "API_SECRET": self._generate_key(),
            # 会话密钥
            "SESSION_KEY": self._generate_key(),
            # OAuth密钥
            "OAUTH_CLIENT_ID": self._generate_key(32),
            "OAUTH_CLIENT_SECRET": self._generate_key(),
            # 其他系统密钥
            "SYSTEM_KEY": self._generate_key(),
            "BACKUP_KEY": self._generate_key(),
        }
        self._save_keys()

    def get_key(self, key_name: str) -> str:
        """获取密钥，如果不存在则生成新密钥"""
        if key_name not in self.keys:
            self.keys[key_name] = self._generate_key()
            self._save_keys()
        return self.keys[key_name]

    def set_key(self, key_name: str, value: str) -> None:
        """设置密钥"""
        self.keys[key_name] = value
        self._save_keys()

    def regenerate_key(self, key_name: str) -> str:
        """重新生成密钥"""
        new_key = self._generate_key()
        self.set_key(key_name, new_key)
        return new_key

    def regenerate_all_keys(self) -> None:
        """重新生成所有密钥"""
        self._generate_all_keys()


# 创建全局密钥管理器实例
key_manager = KeyManager()
