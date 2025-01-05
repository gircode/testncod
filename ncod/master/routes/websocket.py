from fastapi import APIRouter, WebSocket, Depends
from ncod.master.auth import get_current_user
from ncod.master.websocket import ConnectionManager

router = APIRouter()
ws_manager = ConnectionManager()


@router.websocket("/ws/stats/{user_id}")
async def websocket_stats(websocket: WebSocket, user_id: int):
    """统计数据WebSocket连接"""
    try:
        await ws_manager.connect_user(websocket, user_id)

        while True:
            try:
                # 保持连接活跃
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await ws_manager.disconnect_user(websocket, user_id)
