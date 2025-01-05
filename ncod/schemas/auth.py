"""认证相关模式"""

from pydantic import BaseModel


class Token(BaseModel):
    """Token模式"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token数据模式"""

    username: str | None = None
