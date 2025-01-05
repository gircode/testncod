"""WebSocket路由"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ncod.core.logger import setup_logger
from ncod.master.websocket.server import WebSocketServer

router = APIRouter()
ws_server = WebSocketServer()
logger = setup_logger("websocket_routes")


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket端点"""
    await ws_server.connect(websocket, client_id)
    try:
        while True:
            message = await websocket.receive_text()
            await ws_server.handle_message(client_id, message)
    except WebSocketDisconnect:
        await ws_server.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error in websocket connection {client_id}: {e}")
        await ws_server.disconnect(client_id)
