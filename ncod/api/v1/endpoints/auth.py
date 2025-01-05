"""认证相关API端点"""

from datetime import timedelta
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ncod.core.db.base import get_db
from ncod.core.services.auth import AuthService
from ncod.schemas.auth import Token
from ncod.schemas.user import UserCreate
from ncod.models.user import User
from ncod.utils.logger import logger

router = APIRouter()
auth_service = AuthService()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    client_mac: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """用户登录"""
    try:
        user = await auth_service.authenticate_user(
            db, form_data.username, form_data.password
        )

        if client_mac:
            # 验证MAC地址
            if not await auth_service.verify_mac_address(db, user.id, client_mac):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="未授权的设备"
                )
            try:
                # 注册MAC地址
                await auth_service.register_mac_address(db, user.id, client_mac)
            except Exception as e:
                logger.error(f"MAC地址注册失败: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="MAC地址注册失败",
                )

        try:
            access_token = auth_service.create_access_token(data={"sub": str(user.id)})
        except Exception as e:
            logger.error(f"Token生成失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token生成失败",
            )

        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="登录服务异常"
        )


@router.post("/register", response_model=User)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """用户注册"""
    try:
        return await auth_service.create_user(db, user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="用户注册失败"
        )
