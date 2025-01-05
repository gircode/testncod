"""Index模块"""

import datetime
import json
import logging
from typing import Dict, List, Optional

from database import db_manager
from models.user import Device, SystemSetting, Task, User
from pywebio.input import input, input_group, select, textarea
from pywebio.output import clear, put_error, put_html, put_loading, toast
from pywebio.session import info as session_info
from pywebio.session import run_js, set_env

logger = logging.getLogger(__name__)


def get_dashboard_stats() -> Dict:
    """获取仪表盘统计数据"""
    try:
        with db_manager.get_session() as session:
            total_devices = session.query(Device).count()
            online_devices = (
                session.query(Device).filter(Device.status == "online").count()
            )
            total_tasks = session.query(Task).count()
            pending_tasks = session.query(Task).filter(Task.status == "pending").count()
            running_tasks = session.query(Task).filter(Task.status == "running").count()
            failed_tasks = session.query(Task).filter(Task.status == "failed").count()
            total_users = session.query(User).count()

            return {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "offline_devices": total_devices - online_devices,
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "running_tasks": running_tasks,
                "failed_tasks": failed_tasks,
                "total_users": total_users,
            }
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        return {}


def get_recent_tasks(limit: int = 5) -> List[Dict]:
    """获取最近任务"""
    try:
        with db_manager.get_session() as session:
            tasks = (
                session.query(Task).order_by(Task.created_at.desc()).limit(limit).all()
            )

            return [
                {
                    "id": task.id,
                    "name": task.name,
                    "type": task.type,
                    "status": task.status,
                    "device": task.device.name if task.device else None,
                    "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for task in tasks
            ]
    except Exception as e:
        logger.error(f"Failed to get recent tasks: {e}")
        return []


def get_device_status() -> List[Dict]:
    """获取设备状态"""
    try:
        with db_manager.get_session() as session:
            devices = session.query(Device).all()

            return [
                {
                    "id": device.id,
                    "name": device.name,
                    "device_id": device.device_id,
                    "type": device.type,
                    "status": device.status,
                    "ip_address": device.ip_address,
                    "last_heartbeat": (
                        device.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
                        if device.last_heartbeat
                        else None
                    ),
                }
                for device in devices
            ]
    except Exception as e:
        logger.error(f"Failed to get device status: {e}")
        return []


async def index_page():
    """主页面"""
    set_env(title="设备控制管理系统")

    # 页面样式
    style = """
    <style>
        .dashboard {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .dashboard-header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .dashboard-title {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .dashboard-description {
            color: #666;
            font-size: 14px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 32px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .dashboard-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card-title {
            font-size: 18px;
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 15px;
        }
        .task-list {
            margin-top: 10px;
        }
        .task-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }
        .task-item:last-child {
            border-bottom: none;
        }
        .task-info {
            flex: 1;
        }
        .task-name {
            font-weight: 500;
            color: #2c3e50;
        }
        .task-meta {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-online {
            background: #dcfce7;
            color: #16a34a;
        }
        .status-offline {
            background: #fee2e2;
            color: #dc2626;
        }
        .status-error {
            background: #fef3c7;
            color: #d97706;
        }
        .status-pending {
            background: #fef3c7;
            color: #d97706;
        }
        .status-running {
            background: #dbeafe;
            color: #2563eb;
        }
        .status-completed {
            background: #dcfce7;
            color: #16a34a;
        }
        .status-failed {
            background: #fee2e2;
            color: #dc2626;
        }
        .device-list {
            margin-top: 10px;
        }
        .device-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }
        .device-item:last-child {
            border-bottom: none;
        }
        .device-info {
            flex: 1;
        }
        .device-name {
            font-weight: 500;
            color: #2c3e50;
        }
        .device-meta {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .nav-menu {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .nav-button {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
            text-decoration: none;
            text-align: center;
        }
        .nav-button-primary {
            background: #3b82f6;
            color: white;
        }
        .nav-button-primary:hover {
            background: #2563eb;
        }
        .nav-button-secondary {
            background: #e5e7eb;
            color: #374151;
        }
        .nav-button-secondary:hover {
            background: #d1d5db;
        }
    </style>
    """

    # 获取统计数据
    stats = get_dashboard_stats()
    recent_tasks = get_recent_tasks()
    devices = get_device_status()

    # 渲染页面
    clear()
    put_html(style)

    put_html(
        f"""
    <div class="dashboard">
        <div class="dashboard-header">
            <div class="dashboard-title">设备控制管理系统</div>
            <div class="dashboard-description">实时监控和管理您的设备</div>
            <div class="nav-menu">
                <a href="/tasks" class="nav-button nav-button-primary">任务管理</a>
                <a href="/devices" class="nav-button nav-button-primary">设备管理</a>
                <a href="/users" class="nav-button nav-button-primary">用户管理</a>
                <a href="/settings" class="nav-button nav-button-secondary">系统设置</a>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats.get('total_devices', 0)}</div>
                <div class="stat-label">总设备数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('online_devices', 0)}</div>
                <div class="stat-label">在线设备</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('total_tasks', 0)}</div>
                <div class="stat-label">总任务数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('pending_tasks', 0)}</div>
                <div class="stat-label">待处理任务</div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <!-- 最近任务 -->
            <div class="dashboard-card">
                <div class="card-title">最近任务</div>
                <div class="task-list">
    """
    )

    for task in recent_tasks:
        status_class = {
            "pending": "status-pending",
            "running": "status-running",
            "completed": "status-completed",
            "failed": "status-failed",
        }.get(task["status"], "")

        put_html(
            f"""
            <div class="task-item">
                <div class="task-info">
                    <div class="task-name">{task['name']}</div>
                    <div class="task-meta">
                        {task['type']} | 
                        设备: {task['device'] or 'N/A'} | 
                        {task['created_at']}
                    </div>
                </div>
                <span class="status-badge {status_class}">{task['status']}</span>
            </div>
        """
        )

    put_html(
        """
                </div>
            </div>
            
            <!-- 设备状态 -->
            <div class="dashboard-card">
                <div class="card-title">设备状态</div>
                <div class="device-list">
    """
    )

    for device in devices:
        status_class = {
            "online": "status-online",
            "offline": "status-offline",
            "error": "status-error",
        }.get(device["status"], "")

        put_html(
            f"""
            <div class="device-item">
                <div class="device-info">
                    <div class="device-name">{device['name']}</div>
                    <div class="device-meta">
                        {device['type']} | 
                        IP: {device['ip_address']} | 
                        最后心跳: {device['last_heartbeat'] or 'N/A'}
                    </div>
                </div>
                <span class="status-badge {status_class}">{device['status']}</span>
            </div>
        """
        )

    put_html(
        """
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket连接
        const ws = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'stats_update' || data.type === 'device_update' || \
                 data.type === 'task_update') {
                location.reload();
            }
        };
    </script>
    """
    )


if __name__ == "__main__":
    index_page()
