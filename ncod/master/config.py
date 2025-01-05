import os
from datetime import timedelta
from typing import Dict, Any


class Config:
    """基础配置类"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    DEBUG = False
    TESTING = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL'
    ) or 'postgresql://postgres:postgres@localhost/ncod'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Redis配置
    REDIS_URL = os.environ.get(
        'REDIS_URL'
    ) or 'redis://localhost:6379/0'
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.urandom(24).hex()
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS配置
    CORS_ORIGINS = ['http://localhost:3000']
    CORS_SUPPORTS_CREDENTIALS = True
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = (
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    LOG_FILE = 'logs/ncod.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    
    # WebSocket配置
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_PING_TIMEOUT = 10
    SOCKETIO_PING_INTERVAL = 25
    
    # SSL/TLS配置
    SSL_ENABLED = False
    SSL_CERT_FILE = 'certs/cert.pem'
    SSL_KEY_FILE = 'certs/key.pem'
    
    # 备份配置
    BACKUP_ENABLED = True
    BACKUP_INTERVAL = 86400  # 24小时
    BACKUP_KEEP_DAYS = 30
    BACKUP_PATH = 'backups'
    
    # 设备监控配置
    DEVICE_OFFLINE_TIMEOUT = 300  # 5分钟
    SLAVE_OFFLINE_TIMEOUT = 300  # 5分钟
    DEVICE_CHECK_INTERVAL = 60  # 1分钟
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典"""
        config_dict = {}
        for key in dir(cls):
            if not key.startswith('_') and key.isupper():
                config_dict[key] = getattr(cls, key)
        return config_dict


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/ncod_test'
    REDIS_URL = 'redis://localhost:6379/1'
    LOG_FILE = 'logs/test.log'


class ProductionConfig(Config):
    """生产环境配置"""
    CORS_ORIGINS = ['https://example.com']
    SSL_ENABLED = True
    LOG_LEVEL = 'WARNING'
    
    # 生产环境必须设置密钥
    @classmethod
    def init_app(cls) -> None:
        """初始化生产环境配置"""
        required_env = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        for env in required_env:
            if not os.environ.get(env):
                raise RuntimeError(
                    f'Production environment requires {env} to be set'
                )


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 