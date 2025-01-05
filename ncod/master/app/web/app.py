"""App模块"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .api import jwt_config, monitoring
from .api.auth import router as auth_router
from .api.monitoring import router as monitoring_router
from .middleware.auth_middleware import AuthMiddleware

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="监控管理系统", description="用于管理和监控系统指标的Web应用", version="1.0.0"
)

# 添加会话中间件
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key",  # 在生产环境中使用安全的密钥
    session_cookie="ncod_session",
)

# 添加认证中间件
app.middleware("http")(AuthMiddleware())

# 获取当前目录
current_dir = Path(__file__).parent

# 配置静态文件
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")

# 配置模板
templates = Jinja2Templates(directory=str(current_dir / "templates"))

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(monitoring_router, prefix="/api/monitoring", tags=["监控"])
app.include_router(monitoring.router, prefix="/api")
app.include_router(jwt_config.router, prefix="/api")


@app.get("/")
async def index(request: Request):
    """主页 - 重定向到登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard")
async def dashboard(request: Request):
    """仪表盘页面"""
    return templates.TemplateResponse("monitoring.html", {"request": request})
