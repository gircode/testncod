"""
从服务器主程序
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import SLAVE_CONFIG
from .virtualhere_manager import VirtualHereManager
from .device_monitor import DeviceMonitor
from .master_client import MasterClient

app = FastAPI(
    title="NCOD Slave Server",
    description="Network Connected Device Management System - Slave Server",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
vh_manager = VirtualHereManager(SLAVE_CONFIG["virtualhere"])
device_monitor = DeviceMonitor(SLAVE_CONFIG["monitor"])
master_client = MasterClient(SLAVE_CONFIG["master"])


@app.on_event("startup")
async def startup_event():
    """服务启动时的初始化"""
    # 启动VirtualHere服务器
    success = await vh_manager.start_server()
    if not success:
        raise RuntimeError("Failed to start VirtualHere server")

    # 启动设备监控
    await device_monitor.start()

    # 连接主服务器
    await master_client.connect()

    # 启动心跳检测
    asyncio.create_task(heartbeat_loop())


@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭时的清理"""
    # 停止设备监控
    await device_monitor.stop()

    # 断开主服务器连接
    await master_client.disconnect()


async def heartbeat_loop():
    """心跳检测循环"""
    while True:
        try:
            # 获取设备状态
            devices = await vh_manager.get_device_list()

            # 获取系统状态
            system_stats = await device_monitor.get_system_stats()

            # 发送心跳包到主服务器
            await master_client.send_heartbeat(
                {
                    "devices": devices,
                    "system_stats": system_stats,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            print(f"Error in heartbeat loop: {e}")

        await asyncio.sleep(SLAVE_CONFIG["heartbeat_interval"])


# API路由
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "virtualhere": await vh_manager.check_status(),
        "device_count": len(await vh_manager.get_device_list()),
    }


@app.get("/devices")
async def get_devices():
    """获取设备列表"""
    return await vh_manager.get_device_list()


@app.post("/devices/{device_id}/connect")
async def connect_device(device_id: str, user_id: str):
    """连接设备"""
    success = await vh_manager.connect_device(device_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to connect device")
    return {"status": "connected"}


@app.post("/devices/{device_id}/disconnect")
async def disconnect_device(device_id: str):
    """断开设备"""
    success = await vh_manager.disconnect_device(device_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to disconnect device")
    return {"status": "disconnected"}


@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    return {
        "system": await device_monitor.get_system_stats(),
        "devices": await vh_manager.get_device_stats(),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, workers=1)
