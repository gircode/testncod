"""认证API模块"""

import io
import logging
import os
import random
import re
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from ...config.auth_config import UserRole, auth_config
from ...core.exceptions import AuthError
from ...core.jwt import jwt_bearer, jwt_handler
from ...models.audit_log import AuditLogCreate
from ...models.user import UserCreate, UserResponse, UserUpdate
from ...services.audit_service import audit_service
from ...services.user_service import user_service

logger = logging.getLogger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求模型"""

    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=32)
    captcha: str = Field(..., min_length=1, max_length=10)

    class Config:
        json_schema_extra = {
            "example": {"username": "admin", "password": "password123", "captcha": "15"}
        }


class MacAddress(BaseModel):
    """MAC地址模型"""

    mac: str = Field(
        ...,
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        description="MAC地址，格式如：00:11:22:33:44:55",
    )


class TokenResponse(BaseModel):
    """令牌响应模型"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
            }
        }


# 用于存储验证码答案的字典
captcha_store = {}


def generate_math_problem():
    """生成20以内的随机加减法算式"""
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    operator = random.choice(["+", "-"])

    if operator == "-" and b > a:
        a, b = b, a  # 确保减法结果为正数

    result = a + b if operator == "+" else a - b
    problem = f"{a} {operator} {b} = ?"

    return problem, result


def create_captcha_image(text: str) -> bytes:
    """生成验证码图片"""
    # 创建图片
    width = 160
    height = 50
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    # 使用微软雅黑字体
    font_path = str(Path(__file__).parent.parent / "static" / "fonts" / "msyh.ttc")
    font = ImageFont.truetype(font_path, 24)

    # 绘制文本
    text_width = draw.textlength(text, font=font)
    text_height = 24
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, font=font, fill="black")

    # 添加干扰线
    for _ in range(3):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill="gray", width=1)

    # 转换为bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


@router.get("/captcha")
async def get_captcha(request: Request):
    """获取验证码图片"""
    problem, result = generate_math_problem()

    # 将答案存储在session中
    request.session["captcha_result"] = result

    # 生成验证码图片
    image_bytes = create_captcha_image(problem)

    return Response(content=image_bytes, media_type="image/png")


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, login_data: LoginRequest):
    """处理登录请求"""
    try:
        # 验证验证码
        stored_result = request.session.get("captcha_result")
        if not stored_result or int(login_data.captcha) != stored_result:
            raise AuthError("验证码错误，请重新输入")

        # 验证用户
        user = user_service.authenticate_user(login_data.username, login_data.password)

        if not user:
            raise AuthError("用户名或密码错误")

        # 登录成功，清除验证码
        request.session.pop("captcha_result", None)

        # 生成Token
        token_data = {"sub": str(user.id), "username": user.username, "role": user.role}
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)

        # 记录审计日志
        audit_service.log_action(
            AuditLogCreate(
                user_id=user.id,
                action="login",
                resource_type="auth",
                details={"method": "password"},
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
            )
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    except AuthError as e:
        return JSONResponse(
            status_code=400, content={"code": "AUTH_ERROR", "message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": "SYSTEM_ERROR", "message": "系统错误，请稍后重试"},
        )


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer)
):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = jwt_handler.decode_token(credentials.credentials)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="无效的刷新令牌")

        # 生成新的令牌
        token_data = {
            "sub": payload["sub"],
            "username": payload["username"],
            "role": payload["role"],
        }
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)

        # 记录审计日志
        audit_service.log_action(
            AuditLogCreate(
                user_id=int(payload["sub"]),
                action="refresh_token",
                resource_type="auth",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
            )
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer)
):
    """退出登录"""
    try:
        payload = jwt_handler.decode_token(credentials.credentials)

        # 记录审计日志
        audit_service.log_action(
            AuditLogCreate(
                user_id=int(payload["sub"]),
                action="logout",
                resource_type="auth",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
            )
        )

        # 清除session
        request.session.clear()
        return {"message": "退出成功"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


def verify_admin(request: Request):
    """验证管理员权限"""
    session = request.session
    if "user_role" not in session or session["user_role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return True


# 用户管理接口
@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, _: bool = Depends(verify_admin)):
    """创建用户"""
    try:
        return user_service.create_user(user_data)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{username}", response_model=UserResponse)
async def update_user(
    username: str, user_data: UserUpdate, _: bool = Depends(verify_admin)
):
    """更新用户"""
    try:
        return user_service.update_user(username, user_data)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{username}")
async def delete_user(username: str, _: bool = Depends(verify_admin)):
    """删除用户"""
    try:
        user_service.delete_user(username)
        return {"message": "用户删除成功"}
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=list[UserResponse])
async def list_users(_: bool = Depends(verify_admin)):
    """获取用户列表"""
    return user_service.list_users()


@router.get("/users/{username}", response_model=UserResponse)
async def get_user(username: str, _: bool = Depends(verify_admin)):
    """获取用户信息"""
    user = user_service.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


# MAC地址白名单管理接口
@router.post("/mac/whitelist")
async def add_mac_to_whitelist(mac_data: MacAddress, _: bool = Depends(verify_admin)):
    """添加MAC地址到白名单"""
    try:
        # 验证MAC地址格式
        mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        if not mac_pattern.match(mac_data.mac):
            raise HTTPException(status_code=400, detail="无效的MAC地址格式")

        auth_config.add_mac_address(mac_data.mac)
        return {"status": "success", "message": "MAC地址已添加到白名单"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mac/whitelist/{mac}")
async def remove_mac_from_whitelist(mac: str, _: bool = Depends(verify_admin)):
    """从白名单中移除MAC地址"""
    try:
        auth_config.remove_mac_address(mac)
        return {"status": "success", "message": "MAC地址已从白名单中移除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mac/whitelist")
async def get_mac_whitelist(_: bool = Depends(verify_admin)):
    """获取MAC地址白名单"""
    try:
        whitelist = auth_config.get_mac_whitelist()
        return {"mac_addresses": list(whitelist)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
