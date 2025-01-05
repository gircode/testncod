"""Config Validator模块"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """配置验证错误"""

    pass


class DatabaseConfig(BaseModel):
    """数据库配置验证模型"""

    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int


class RedisConfig(BaseModel):
    """Redis配置验证模型"""

    url: str
    db: int
    password: str = None
    pool_size: int


class SecurityConfig(BaseModel):
    """安全配置验证模型"""

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


class LoggingConfig(BaseModel):
    """日志配置验证模型"""

    level: str
    format: str
    file: str
    max_size: str
    backup_count: int


class Config(BaseModel):
    """主配置验证模型"""

    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    logging: LoggingConfig


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """加载YAML配置文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ConfigValidationError(f"Failed to load YAML config: {e}")


def load_json_config(file_path: str) -> Dict[str, Any]:
    """加载JSON配置文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ConfigValidationError(f"Failed to load JSON config: {e}")


def validate_config(config_data: Dict[str, Any]) -> Config:
    """验证配置数据"""
    try:
        return Config(**config_data)
    except ValidationError as e:
        raise ConfigValidationError(f"Config validation failed: {e}")


def check_file_permissions(file_path: str) -> List[str]:
    """检查文件权限"""
    issues = []
    path = Path(file_path)

    if not path.exists():
        issues.append(f"File does not exist: {file_path}")
        return issues

    # 检查文件权限
    mode = path.stat().st_mode
    if mode & 0o077:  # 检查组和其他用户的权限
        issues.append(f"File has too broad permissions: {oct(mode)}")

    # 检查所有者
    if os.name != "nt":  # 在Unix系统上检查
        import pwd

        owner = pwd.getpwuid(path.stat().st_uid).pw_name
        if owner != "root":
            issues.append(f"File not owned by root: {owner}")

    return issues


def validate_environment_variables(required_vars: List[str]) -> List[str]:
    """验证环境变量"""
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    return missing


def check_directory_permissions(dir_path: str) -> List[str]:
    """检查目录权限"""
    issues = []
    path = Path(dir_path)

    if not path.exists():
        issues.append(f"Directory does not exist: {dir_path}")
        return issues

    if not path.is_dir():
        issues.append(f"Path is not a directory: {dir_path}")
        return issues

    # 检查目录权限
    mode = path.stat().st_mode
    if mode & 0o022:  # 检查组和其他用户的写权限
        issues.append(f"Directory has too broad permissions: {oct(mode)}")

    return issues


def validate_config_file(file_path: str) -> Dict[str, Any]:
    """验证配置文件"""
    # 检查文件扩展名
    ext = Path(file_path).suffix.lower()

    # 检查文件权限
    permission_issues = check_file_permissions(file_path)
    if permission_issues:
        for issue in permission_issues:
            logger.warning(issue)

    # 加载并验证配置
    try:
        if ext == ".yaml" or ext == ".yml":
            config_data = load_yaml_config(file_path)
        elif ext == ".json":
            config_data = load_json_config(file_path)
        else:
            raise ConfigValidationError(f"Unsupported config file format: {ext}")

        # 验证配置数据
        config = validate_config(config_data)

        # 检查日志目录权限
        log_dir = os.path.dirname(config.logging.file)
        dir_issues = check_directory_permissions(log_dir)
        if dir_issues:
            for issue in dir_issues:
                logger.warning(issue)

        return config_data

    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        raise


def migrate_config(
    old_config: Dict[str, Any], new_config: Dict[str, Any]
) -> Dict[str, Any]:
    """迁移配置"""
    # 创建配置备份
    backup_path = f"{Path(old_config).parent}/config.backup.{int(time.time())}"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(old_config, f, indent=2)

    # 合并配置
    merged = old_config.copy()
    merged.update(new_config)

    # 验证合并后的配置
    validate_config(merged)

    return merged


def generate_default_config() -> Dict[str, Any]:
    """生成默认配置"""
    return {
        "database": {
            "url": "postgresql+asyncpg://user:pass@localhost/dbname",
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
        },
        "redis": {"url": "redis://localhost", "db": 0, "pool_size": 10},
        "security": {
            "secret_key": "",  # 需要生成
            "algorithm": "HS256",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_days": 7,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "/var/log/ncod/app.log",
            "max_size": "100MB",
            "backup_count": 30,
        },
    }
