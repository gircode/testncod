"""从服务器路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ncod.core.deps import get_current_active_admin
from ncod.core.logger import master_logger as logger
from ncod.master.models.user import User
from ncod.master.services.slave import SlaveService
from ncod.master.schemas.slave import (
    SlaveCreate,
    SlaveUpdate,
    SlaveResponse,
    SlaveStatus,
)

router = APIRouter()
slave_service = SlaveService()


@router.get("/", response_model=List[SlaveResponse])
async def get_slaves(
    current_user: User = Depends(get_current_active_admin),
    skip: int = 0,
    limit: int = 100,
):
    """获取从服务器列表"""
    try:
        slaves = await slave_service.get_slaves(skip=skip, limit=limit)
        return slaves
    except Exception as e:
        logger.error(f"Error getting slaves: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get slaves",
        )


@router.post("/", response_model=SlaveResponse)
async def register_slave(
    slave: SlaveCreate, current_user: User = Depends(get_current_active_admin)
):
    """注册从服务器"""
    try:
        return await slave_service.register_slave(slave)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering slave: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register slave",
        )


@router.get("/{slave_id}", response_model=SlaveResponse)
async def get_slave(
    slave_id: str, current_user: User = Depends(get_current_active_admin)
):
    """获取从服务器详情"""
    slave = await slave_service.get_slave(slave_id)
    if not slave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Slave not found"
        )
    return slave


@router.put("/{slave_id}", response_model=SlaveResponse)
async def update_slave(
    slave_id: str,
    slave_update: SlaveUpdate,
    current_user: User = Depends(get_current_active_admin),
):
    """更新从服务器"""
    try:
        slave = await slave_service.update_slave(slave_id, slave_update)
        if not slave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Slave not found"
            )
        return slave
    except Exception as e:
        logger.error(f"Error updating slave: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update slave",
        )


@router.get("/{slave_id}/status", response_model=SlaveStatus)
async def get_slave_status(
    slave_id: str, current_user: User = Depends(get_current_active_admin)
):
    """获取从服务器状态"""
    try:
        status = await slave_service.get_slave_status(slave_id)
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Slave not found"
            )
        return status
    except Exception as e:
        logger.error(f"Error getting slave status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get slave status",
        )
