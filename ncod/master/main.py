import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import API_CONFIG
from .websocket.server import websocket_server
from .routes import api_router
from .database import init_models

app = FastAPI(
    title="NCOD Master Server",
    description="Network Connected Device Management System - Master Server",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket连接端点"""
    user_id = await get_user_id_from_token(websocket)
    if not user_id:
        await websocket.close(code=4001)
        return

    await websocket_server.handle_connection(websocket, client_id, user_id)


@app.on_event("startup")
async def startup_event():
    """服务启动时的初始化"""
    # 初始化数据库模型
    await init_models()

    # 启动WebSocket服务器
    await websocket_server.start()

    # 启动设备监控
    from .monitoring.collector import start_monitoring

    asyncio.create_task(start_monitoring())


@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭时的清理"""
    # 停止WebSocket服务器
    await websocket_server.stop()

    # 清理数据库连接
    from .database import cleanup_db

    await cleanup_db()


async def get_user_id_from_token(websocket: WebSocket) -> str:
    """从Token中获取用户ID"""
    try:
        token = websocket.headers.get("authorization", "").split(" ")[1]
        from .core.auth import decode_jwt_token

        payload = await decode_jwt_token(token)
        return payload.get("user_id")
    except Exception as e:
        print(f"Error getting user ID from token: {e}")
        return None


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=4)
