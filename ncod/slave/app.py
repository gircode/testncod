"""从服务器入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ncod.utils.config import settings
from ncod.utils.logger import setup_logger

logger = setup_logger(__name__)

# 创建应用实例
app = FastAPI(
    title="NCOD Slave API",
    description="Network Connected Open Device Slave API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
# TODO: 添加路由导入


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("从服务器启动")
    # TODO: 添加启动时的初始化代码


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("从服务器关闭")
    # TODO: 添加关闭时的清理代码
