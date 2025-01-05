"""Devices模块"""

import datetime
import json
import logging

from database import db_manager
from models.user import Device, DeviceMetric, Task
from pywebio.input import input, input_group, select
from pywebio.output import clear, put_error, put_html, put_loading, toast
from pywebio.session import info as session_info
from pywebio.session import run_js, set_env

logger = logging.getLogger(__name__)


def get_device_details(device_id: str):
    """获取设备详细信息"""
    try:
        with db_manager.get_session() as session:
            device = session.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return None

            # 获取最近的指标
            recent_metrics = (
                session.query(DeviceMetric)
                .filter(
                    DeviceMetric.device_id == device.id,
                    DeviceMetric.collected_at
                    >= datetime.datetime.utcnow() - datetime.timedelta(hours=1),
                )
                .order_by(DeviceMetric.collected_at.desc())
                .all()
            )

            # 获取相关任务
            recent_tasks = (
                session.query(Task)
                .filter(Task.device_id == device.id)
                .order_by(Task.created_at.desc())
                .limit(10)
                .all()
            )

            return {
                "device": {
                    "id": device.id,
                    "name": device.name,
                    "device_id": device.device_id,
                    "type": device.type,
                    "status": device.status,
                    "ip_address": device.ip_address,
                    "last_heartbeat": (
                        device.last_heartbeat.isoformat()
                        if device.last_heartbeat
                        else None
                    ),
                    "config": device.config,
                },
                "metrics": [
                    {
                        "type": metric.metric_type,
                        "value": metric.value,
                        "time": metric.collected_at.isoformat(),
                    }
                    for metric in recent_metrics
                ],
                "tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "type": task.type,
                        "status": task.status,
                        "created_at": task.created_at.isoformat(),
                    }
                    for task in recent_tasks
                ],
            }
    except Exception as e:
        logger.error(f"Failed to get device details: {e}")
        return None


async def add_device():
    """添加新设备"""
    try:
        data = await input_group(
            "添加设备",
            [
                input("设备名称", name="name", required=True),
                input("设备ID", name="device_id", required=True),
                select(
                    "设备类型",
                    name="type",
                    options=[
                        {"label": "主服务器", "value": "master"},
                        {"label": "从服务器", "value": "slave"},
                    ],
                ),
                input("IP地址", name="ip_address", required=True),
                input(
                    "配置", name="config", type="text", placeholder="JSON格式的配置信息"
                ),
            ],
        )

        # 验证配置JSON
        try:
            config = json.loads(data["config"]) if data["config"] else {}
        except json.JSONDecodeError:
            toast("配置信息必须是有效的JSON格式")
            return

        # 创建设备
        with db_manager.get_session() as session:
            device = Device(
                name=data["name"],
                device_id=data["device_id"],
                type=data["type"],
                status="offline",
                ip_address=data["ip_address"],
                config=config,
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            session.add(device)
            session.commit()

        toast("设备添加成功")
        return True

    except Exception as e:
        logger.error(f"Failed to add device: {e}")
        toast("添加设备失败")
        return False


async def devices():
    """设备管理页面"""
    set_env(title="设备管理")

    # 页面样式
    style = """
    <style>
        .devices-container {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .device-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .device-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
        .device-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .device-name {
            font-size: 18px;
            font-weight: 500;
            color: #2c3e50;
        }
        .device-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
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
        .device-info {
            margin: 10px 0;
            font-size: 14px;
            color: #666;
        }
        .device-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .action-button {
            padding: 6px 12px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        .view-button {
            background: #3b82f6;
            color: white;
        }
        .edit-button {
            background: #10b981;
            color: white;
        }
        .delete-button {
            background: #ef4444;
            color: white;
        }
        .add-device-button {
            display: block;
            width: 100%;
            padding: 12px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
            margin-bottom: 20px;
        }
        .add-device-button:hover {
            background: #2563eb;
        }
        .device-metrics {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
        }
        .metric-item {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            font-size: 14px;
        }
        .metric-label {
            color: #666;
        }
        .metric-value {
            font-weight: 500;
            color: #2c3e50;
        }
    </style>
    """

    # 渲染页面
    clear()
    put_html(style)

    put_html(
        """
    <div class="devices-container">
        <button class="add-device-button" onclick="addDevice()">添加设备</button>
        <div class="device-list">
    """
    )

    # 获取并显示设备列表
    try:
        with db_manager.get_session() as session:
            devices = session.query(Device).all()
            for device in devices:
                status_class = {
                    "online": "status-online",
                    "offline": "status-offline",
                    "error": "status-error",
                }.get(device.status, "")

                # 获取最新的指标
                latest_metrics = (
                    session.query(DeviceMetric)
                    .filter(DeviceMetric.device_id == device.id)
                    .order_by(DeviceMetric.collected_at.desc())
                    .limit(3)
                    .all()
                )

                put_html(
                    f"""
                    <div class="device-card">
                        <div class="device-header">
                            <span class="device-name">{device.name}</span>
                            <span class="device-status \
                                 {status_class}">{device.status}</span>
                        </div>
                        <div class="device-info">
                            <p>ID: {device.device_id}</p>
                            <p>类型: {device.type}</p>
                            <p>IP: {device.ip_address}</p>
                            <p>最后心跳: {device.last_heartbeat.strftime('%Y-%m-%d \
                                 %H:%M:%S') if device.last_heartbeat else 'N/A'}</p>
                        </div>
                        <div class="device-metrics">
                """
                )

                for metric in latest_metrics:
                    put_html(
                        f"""
                        <div class="metric-item">
                            <span class="metric-label">{metric.metric_type}</span>
                            <span class="metric-value">{json.dumps(metric.value)}</span>
                        </div>
                    """
                    )

                put_html(
                    f"""
                        </div>
                        <div class="device-actions">
                            <button class="action-button view-button" \
                                 onclick="viewDevice('{device.device_id}')">查看</button>
                            <button class="action-button edit-button" \
                                 onclick="editDevice('{device.device_id}')">编辑</button>
                            <button class="action-button delete-button" \
                                 onclick="deleteDevice('{device.device_id}')">删除</button>
                        </div>
                    </div>
                """
                )
    except Exception as e:
        logger.error(f"Failed to load devices: {e}")
        put_error("加载设备列表失败")

    # 添加JavaScript函数
    put_html(
        """
        </div>
    </div>
    <script>
        function addDevice() {
            pywebio.call_js_function("add_device");
        }
        
        function viewDevice(deviceId) {
            window.location.href = `/device/${deviceId}`;
        }
        
        function editDevice(deviceId) {
            window.location.href = `/device/${deviceId}/edit`;
        }
        
        function deleteDevice(deviceId) {
            if (confirm('确定要删除此设备吗？')) {
                pywebio.call_js_function("delete_device", deviceId);
            }
        }
    </script>
    """
    )


if __name__ == "__main__":
    devices()
