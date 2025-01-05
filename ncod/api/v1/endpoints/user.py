"""用户相关API端点"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.db.base import get_db
from ....core.services.user import UserService
from ....middleware.auth import get_current_user
from ....models.user import User
from ....schemas.auth import UserCreate, UserUpdate
from ....utils.logger import logger

router = APIRouter()
user_service = UserService()


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> User:
    """获取当前用户信息"""
    return current_user


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取用户信息"""
    try:
        if not current_user.is_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此用户信息"
            )
        user = await user_service.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )
        return user
    except Exception as e:
        logger.error("获取用户信息失败", exc_info=True)
        raise


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """更新用户信息"""
    try:
        if not current_user.is_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此用户信息"
            )
        return await user_service.update_user(db, user_id, user_data)
    except Exception as e:
        logger.error("更新用户信息失败", exc_info=True)
        raise
