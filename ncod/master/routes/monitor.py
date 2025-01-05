from fastapi import APIRouter, Depends, WebSocket, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ncod.common.services.monitor import system_monitor
from ncod.common.services.websocket import websocket_manager
from ncod.core.auth import get_current_user
from ncod.core.database import get_db
from ncod.schemas.device import DeviceResponse
from ncod.utils.logger import logger
from ncod.models.device import Device

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db)
):
    try:
        # 验证用户
        user = await get_current_user(token, db)
        if not user:
            await websocket.close(code=4001)
            return

        # 建立连接
        await websocket_manager.connect(websocket, user.id)

        try:
            while True:
                data = await websocket.receive_text()
                # 处理接收到的消息
                await websocket_manager.send_personal_message(
                    {"type": "echo", "data": data}, user.id
                )
        except Exception as e:
            logger.error(f"WebSocket连接异常: {str(e)}")
        finally:
            await websocket_manager.disconnect(websocket, user.id)

    except Exception as e:
        logger.error(f"WebSocket endpoint异常: {str(e)}")
        await websocket.close(code=4000)


@router.get("/metrics")
async def get_metrics(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """获取系统指标"""
    try:
        metrics = await system_monitor.get_system_metrics()
        return {"status": "success", "data": metrics}
    except Exception as e:
        logger.error(f"获取系统指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统指标失败")


@router.get("/devices")
async def get_devices(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> List[DeviceResponse]:
    """获取设备列表"""
    try:
        devices = await Device.get_all(db)
        return [DeviceResponse.from_orm(device) for device in devices]
    except Exception as e:
        logger.error(f"获取设备列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取设备列表失败")
