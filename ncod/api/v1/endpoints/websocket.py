"""WebSocket相关API端点"""

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
)

from ncod.core.auth import get_current_user
from ncod.core.websocket import websocket_manager
from ncod.utils.logger import logger

router = APIRouter()


@router.websocket("/device/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: int, token: str):
    """WebSocket连接端点"""
    try:
        # 验证token
        user = await get_current_user(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 建立连接
        await websocket_manager.connect(device_id, websocket)

        try:
            while True:
                # 接收消息
                data = await websocket.receive_json()
                # 广播消息
                await websocket_manager.broadcast(device_id, data)
        except WebSocketDisconnect:
            # 断开连接
            await websocket_manager.disconnect(device_id, websocket)
        except Exception as e:
            logger.error(f"WebSocket处理消息失败: {str(e)}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    except Exception as e:
        logger.error(f"WebSocket连接失败: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
