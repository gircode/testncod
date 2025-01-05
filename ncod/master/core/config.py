from pydantic import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "ncod"

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # 心跳配置
    HEARTBEAT_TIMEOUT: int = 30
    HEARTBEAT_RETRY_LIMIT: int = 3

    # 服务器配置
    MASTER_ID: str = "master-1"
    DISCOVERY_PORT: int = 5000

    # VirtualHere配置
    VH_SERVER_HOST: str = "localhost"
    VH_SERVER_PORT: int = 7575
