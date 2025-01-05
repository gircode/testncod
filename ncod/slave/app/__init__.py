"""从服务器应用"""

from fastapi import FastAPI
from ncod.core.config import config


class App:
    """从服务器应用类"""

    def __init__(self):
        self.app = FastAPI(
            title="NCOD Slave Server",
            description="NCOD从服务器",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )
        self._init_routes()

    def _init_routes(self):
        """初始化路由"""
        from ncod.slave.routes import device, health

        self.app.include_router(device.router)
        self.app.include_router(health.router)

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


def create_app() -> FastAPI:
    """创建应用"""
    app = App()
    return app.get_app()


def run():
    """运行应用"""
    import uvicorn

    uvicorn.run(
        "ncod.slave.app:create_app()",
        host="0.0.0.0",
        port=config.SLAVE_PORT,
        reload=config.DEBUG,
    )
