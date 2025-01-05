"""Device Groups模块"""

import datetime
import json

from database import db_manager
from models.user import Device, DeviceGroup
from pywebio.input import checkbox, input, input_group, select
from pywebio.output import clear, put_error, put_html, put_loading, toast
from pywebio.session import set_env


async def create_device_group():
    """创建设备组"""
    try:
        with db_manager.get_session() as session:
            # 获取可用设备列表
            devices = session.query(Device).all()
            device_options = [
                {"label": f"{d.name} ({d.device_id})", "value": d.id} for d in devices
            ]

            data = await input_group(
                "创建设备组",
                [
                    input("组名称", name="name", required=True),
                    input("描述", name="description", type="text"),
                    checkbox("选择设备", name="device_ids", options=device_options),
                    input("标签", name="tags", placeholder="用逗号分隔的标签"),
                ],
            )

            # 创建设备组
            group = DeviceGroup(
                name=data["name"],
                description=data["description"],
                tags=data["tags"].split(",") if data["tags"] else [],
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            session.add(group)
            session.flush()

            # 关联设备
            if data["device_ids"]:
                for device_id in data["device_ids"]:
                    device = session.query(Device).get(device_id)
                    if device:
                        group.devices.append(device)

            session.commit()
            toast("设备组创建成功")
            return True

    except Exception as e:
        toast(f"创建设备组失败: {str(e)}")
        return False


async def batch_operation(group_id: int, operation: str, params: dict = None):
    """执行批量操作"""
    try:
        with db_manager.get_session() as session:
            group = session.query(DeviceGroup).get(group_id)
            if not group:
                return False

            for device in group.devices:
                if operation == "update_config":
                    device.config.update(params.get("config", {}))
                elif operation == "restart":
                    # 创建重启任务
                    task = Task(
                        device_id=device.id,
                        type="restart",
                        status="pending",
                        created_at=datetime.datetime.utcnow(),
                    )
                    session.add(task)
                elif operation == "update_status":
                    device.status = params.get("status")

                device.updated_at = datetime.datetime.utcnow()

            session.commit()
            toast(f"批量操作 {operation} 执行成功")
            return True

    except Exception as e:
        toast(f"批量操作失败: {str(e)}")
        return False


async def device_groups():
    """设备组管理页面"""
    set_env(title="设备组管理")

    # 页面样式
    style = """
    <style>
        .groups-container {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .group-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .group-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .group-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .group-name {
            font-size: 18px;
            font-weight: 500;
        }
        .group-stats {
            display: flex;
            gap: 15px;
            margin: 10px 0;
        }
        .stat-item {
            font-size: 14px;
            color: #666;
        }
        .group-actions {
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
        .create-group-button {
            display: block;
            width: 100%;
            padding: 12px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .tags-container {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin: 10px 0;
        }
        .tag {
            background: #e5e7eb;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            color: #4b5563;
        }
    </style>
    """

    clear()
    put_html(style)

    # 添加创建按钮
    put_html(
        """
    <div class="groups-container">
        <button class="create-group-button" onclick="createDeviceGroup()">创建设备组</button>
    """
    )

    try:
        with db_manager.get_session() as session:
            groups = session.query(DeviceGroup).all()

            for group in groups:
                device_count = len(group.devices)
                online_count = sum(1 for d in group.devices if d.status == "online")

                put_html(
                    f"""
                <div class="group-card">
                    <div class="group-header">
                        <span class="group-name">{group.name}</span>
                    </div>
                    <div class="group-stats">
                        <span class="stat-item">设备数: {device_count}</span>
                        <span class="stat-item">在线: {online_count}</span>
                    </div>
                    <div class="tags-container">
                        {''.join(f'<span class="tag">{tag}</span>' for tag in \
                             group.tags)}
                    </div>
                    <p class="group-description">{group.description or ''}</p>
                    <div class="group-actions">
                        <button class="action-button" \
                             onclick="batchOperation({group.id}, \
                                  'restart')">批量重启</button>
                        <button class="action-button" \
                             onclick="batchOperation({group.id}, \
                                  'update_config')">批量配置</button>
                        <button class="action-button" \
                             onclick="editGroup({group.id})">编辑</button>
                    </div>
                </div>
                """
                )

    except Exception as e:
        put_error(f"加载设备组失败: {str(e)}")

    put_html("</div>")


if __name__ == "__main__":
    device_groups()
