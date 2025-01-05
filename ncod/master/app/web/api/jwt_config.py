"""Jwt Config模块"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...core.jwt import JWT_CONFIG

router = APIRouter()
templates = Jinja2Templates(directory="master/app/web/templates")


@router.get("/jwt-config", response_class=HTMLResponse)
async def jwt_config(request: Request):
    """显示JWT配置信息页面"""
    return templates.TemplateResponse(
        "jwt_config.html", {"request": request, "config": JWT_CONFIG}
    )
