"""
配置相关路由
"""

from typing import Any, Dict, List, Optional

from app.core.deps import get_current_active_user, get_current_user
from app.core.security import check_admin_permission
from app.db.session import get_db
from app.models.auth import User
from app.schemas.config import ConfigCreate, ConfigResponse, ConfigSearch, ConfigUpdate
from app.services.config import ConfigService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=List[ConfigResponse],
    summary="获取配置列表",
    description="""
    获取系统配置列表。
    
    需要管理员权限。
    """,
    responses={
        200: {
            "description": "成功获取配置列表",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "key": "max_users",
                            "value": "100",
                            "description": "最大用户数",
                            "group": "system",
                            "is_secret": False,
                            "created_at": "2024-01-20T10:30:00",
                        }
                    ]
                }
            },
        },
        403: {"description": "权限不足"},
    },
)
async def get_configs(
    search: ConfigSearch = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConfigResponse]:
    """
    获取配置列表

    - **search**: 搜索条件
    """
    if not await check_admin_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )

    config_service = ConfigService(db)
    configs = await config_service.get_configs(search)
    return [ConfigResponse.from_orm(config) for config in configs]


@router.post(
    "/",
    response_model=ConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建配置",
    description="""
    创建新的系统配置。
    
    需要管理员权限。
    """,
    responses={
        201: {
            "description": "成功创建配置",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "key": "max_users",
                        "value": "100",
                        "description": "最大用户数",
                        "group": "system",
                        "is_secret": False,
                        "created_at": "2024-01-20T10:30:00",
                    }
                }
            },
        },
        403: {"description": "权限不足"},
        409: {"description": "配置已存在"},
    },
)
async def create_config(
    config_in: ConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConfigResponse:
    """
    创建配置

    - **config_in**: 配置信息
    """
    if not await check_admin_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )

    config_service = ConfigService(db)
    config = await config_service.create_config(config_in)
    return ConfigResponse.from_orm(config)


@router.get(
    "/{key}",
    response_model=ConfigResponse,
    summary="获取配置详情",
    description="""
    获取指定配置的详细信息。
    
    需要管理员权限。
    """,
    responses={
        200: {
            "description": "成功获取配置详情",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "key": "max_users",
                        "value": "100",
                        "description": "最大用户数",
                        "group": "system",
                        "is_secret": False,
                        "created_at": "2024-01-20T10:30:00",
                    }
                }
            },
        },
        403: {"description": "权限不足"},
        404: {"description": "配置不存在"},
    },
)
async def get_config(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConfigResponse:
    """
    获取配置详情

    - **key**: 配置键
    """
    if not await check_admin_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )

    config_service = ConfigService(db)
    config = await config_service.get_config(key)

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")

    return ConfigResponse.from_orm(config)


@router.put(
    "/{key}",
    response_model=ConfigResponse,
    summary="更新配置",
    description="""
    更新指定配置的信息。
    
    需要管理员权限。
    """,
    responses={
        200: {
            "description": "成功更新配置",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "key": "max_users",
                        "value": "200",
                        "description": "最大用户数",
                        "group": "system",
                        "is_secret": False,
                        "created_at": "2024-01-20T10:30:00",
                    }
                }
            },
        },
        403: {"description": "权限不足"},
        404: {"description": "配置不存在"},
    },
)
async def update_config(
    key: str,
    config_in: ConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConfigResponse:
    """
    更新配置

    - **key**: 配置键
    - **config_in**: 更新的配置信息
    """
    if not await check_admin_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )

    config_service = ConfigService(db)
    config = await config_service.update_config(key, config_in)

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")

    return ConfigResponse.from_orm(config)


@router.delete(
    "/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除配置",
    description="""
    删除指定的配置。
    
    需要管理员权限。
    """,
    responses={
        204: {"description": "成功删除配置"},
        403: {"description": "权限不足"},
        404: {"description": "配置不存在"},
    },
)
async def delete_config(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    删除配置

    - **key**: 配置键
    """
    if not await check_admin_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )

    config_service = ConfigService(db)
    deleted = await config_service.delete_config(key)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
