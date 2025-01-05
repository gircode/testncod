"""配置验证"""

from typing import Dict, Any
from pydantic import BaseModel, ValidationError


class ConfigValidator(BaseModel):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    LOG_LEVEL: str

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> None:
        try:
            cls(**config)
        except ValidationError as e:
            raise ValueError(f"配置验证失败: {str(e)}")
