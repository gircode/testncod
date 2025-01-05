"""认证Schema定义"""

from typing import Optional
from pydantic import BaseModel, Field
from ncod.master.schemas.user import UserResponse


class Token(BaseModel):
    """令牌Schema"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")


class TokenData(BaseModel):
    """令牌数据Schema"""

    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    organization_id: str = Field(..., description="组织ID")
    exp: Optional[int] = Field(None, description="过期时间")


class LoginRequest(BaseModel):
    """登录请求Schema"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=64)


class LoginResponse(BaseModel):
    """登录响应Schema"""

    token: Token
    user: UserResponse
