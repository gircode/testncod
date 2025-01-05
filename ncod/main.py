"""主应用模块"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ncod.api.v1.endpoints import auth, monitor
from ncod.utils.logger import logger
from ncod.core.log import configure_logging

app = FastAPI(title="NCOD API", description="NCOD System API", version="0.1.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(monitor.router, prefix="/api/v1/monitor", tags=["监控"])


@app.on_event("startup")
async def startup_event():
    """应用启动时的处理"""
    logger.info("应用启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的处理"""
    logger.info("应用关闭")


def main():
    """主函数"""
    # 配置日志系统
    configure_logging()

    # ... 其他初始化代码
