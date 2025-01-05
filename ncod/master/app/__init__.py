"""主服务器应用"""

from fastapi import FastAPI
from ncod.core.config import config


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="NCOD Master Server",
        description="NCOD主服务器",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 注册路由
    from ncod.master.routes import device, auth, monitor

    app.include_router(device.router)
    app.include_router(auth.router)
    app.include_router(monitor.router)

    return app


# 创建应用实例
app = create_app()
