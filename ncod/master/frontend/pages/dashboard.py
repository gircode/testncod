"""
Dashboard Page
"""

from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render dashboard page"""
    context = {
        "request": request,
        "title": "Dashboard",
        "metrics": {
            "active_users": 100,
            "total_tasks": 500,
            "running_tasks": 50,
            "completed_tasks": 400,
        },
    }
    return templates.TemplateResponse("dashboard.html", context)
