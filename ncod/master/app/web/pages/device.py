"""
设备管理页面
"""

from typing import Any, Dict, List

from pywebio.output import put_html, put_loading
from pywebio.pin import pin

from ...core.auth import require_auth
from ...services.device import DeviceService
from ..components.chart import create_dashboard
from ..components.layout import page_layout
from ..components.notification import show_error, show_success
from ..components.table import create_crud_table


@page_layout(title="设备管理")
@require_auth
async def device_page() -> None:
    """设备管理页面"""
    try:
        service = DeviceService()

        # 获取设备列表
        devices = await service.get_devices()

        # 获取设备统计信息
        stats = await service.get_device_stats()

        # 创建仪表板
        create_dashboard(
            charts=[
                {"type": "gauge", "title": "设备在线率", "value": stats["online_rate"]},
                {
                    "type": "pie",
                    "title": "设备状态分布",
                    "data": [
                        {"name": "在线", "value": stats["online_count"]},
                        {"name": "离线", "value": stats["offline_count"]},
                        {"name": "故障", "value": stats["error_count"]},
                    ],
                    "name_field": "name",
                    "value_field": "value",
                },
                {
                    "type": "bar",
                    "title": "设备使用率",
                    "data": stats["usage_data"],
                    "x_field": "device_name",
                    "y_field": "usage_rate",
                },
                {
                    "type": "line",
                    "title": "设备活动趋势",
                    "data": stats["activity_data"],
                    "x_field": "time",
                    "y_field": "active_count",
                },
            ]
        )

        # 创建设备表格
        create_crud_table(
            model="设备",
            headers=[
                "ID",
                "名称",
                "类型",
                "状态",
                "所属组",
                "从服务器",
                "最后活动时间",
            ],
            data=[
                {
                    "id": device.id,
                    "name": device.name,
                    "type": device.type,
                    "status": device.status,
                    "group": device.group.name if device.group else "-",
                    "slave": (
                        f"{device.slave_server.host}:{device.slave_server.port}"
                        if device.slave_server
                        else "-"
                    ),
                    "last_active": (
                        device.last_active.strftime("%Y-%m-%d %H:%M:%S")
                        if device.last_active
                        else "-"
                    ),
                }
                for device in devices
            ],
            create_form={
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "label": "设备名称",
                        "required": True,
                    },
                    {
                        "name": "type",
                        "type": "select",
                        "label": "设备类型",
                        "options": [
                            {"label": "USB设备", "value": "usb"},
                            {"label": "串口设备", "value": "serial"},
                            {"label": "网络设备", "value": "network"},
                        ],
                        "required": True,
                    },
                    {
                        "name": "group_id",
                        "type": "select",
                        "label": "所属组",
                        "options": await service.get_group_options(),
                    },
                    {
                        "name": "slave_id",
                        "type": "select",
                        "label": "从服务器",
                        "options": await service.get_slave_options(),
                    },
                ],
                "on_create": service.create_device,
            },
            edit_form={
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "label": "设备名称",
                        "required": True,
                    },
                    {
                        "name": "type",
                        "type": "select",
                        "label": "设备类型",
                        "options": [
                            {"label": "USB设备", "value": "usb"},
                            {"label": "串口设备", "value": "serial"},
                            {"label": "网络设备", "value": "network"},
                        ],
                        "required": True,
                    },
                    {
                        "name": "group_id",
                        "type": "select",
                        "label": "所属组",
                        "options": await service.get_group_options(),
                    },
                    {
                        "name": "slave_id",
                        "type": "select",
                        "label": "从服务器",
                        "options": await service.get_slave_options(),
                    },
                ],
                "get_data": service.get_device,
                "on_edit": service.update_device,
            },
        )

    except Exception as e:
        show_error(f"加载设备管理页面失败: {str(e)}")


@page_layout(title="设备详情")
@require_auth
async def device_detail_page(device_id: int) -> None:
    """设备详情页面

    Args:
        device_id: 设备ID
    """
    try:
        service = DeviceService()

        # 获取设备信息
        device = await service.get_device(device_id)
        if not device:
            show_error("设备不存在")
            return

        # 获取设备使用记录
        usage_records = await service.get_device_usage_history(device_id)

        # 获取设备监控数据
        monitor_data = await service.get_device_monitor_data(device_id)

        # 创建设备信息卡片
        put_html(
            f"""
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">设备信息</h5>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>设备名称：</strong>{device.name}</p>
                        <p><strong>设备类型：</strong>{device.type}</p>
                        <p><strong>设备状态：</strong>{device.status}</p>
                        <p><strong>所属组：</strong>{device.group.name if device.group else \
                             "-"}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>从服务器：</strong>{device.slave_server.host}:{device.slave_server.port if device.slave_server else "-"}</p>
                        <p><strong>最后活动时间：</strong>{device.last_active.strftime("%Y-%m-%d %H:%M:%S") if device.last_active else "-"}</p>
                        <p><strong>创建时间：</strong>{device.created_at.strftime("%Y-%m-%d \
                             %H:%M:%S")}</p>
                        <p><strong>更新时间：</strong>{device.updated_at.strftime("%Y-%m-%d \
                             %H:%M:%S")}</p>
                    </div>
                </div>
            </div>
        </div>
        """
        )

        # 创建设备监控图表
        create_dashboard(
            charts=[
                {
                    "type": "line",
                    "title": "CPU使用率",
                    "data": monitor_data["cpu_usage"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "line",
                    "title": "内存使用率",
                    "data": monitor_data["memory_usage"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "line",
                    "title": "网络流量",
                    "data": monitor_data["network_traffic"],
                    "x_field": "time",
                    "y_field": "value",
                },
            ]
        )

        # 创建使用记录表格
        create_crud_table(
            model="使用记录",
            headers=["ID", "用户", "开始时间", "结束时间", "使用时长", "状态"],
            data=[
                {
                    "id": record.id,
                    "user": record.user.username,
                    "start_time": record.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": (
                        record.end_time.strftime("%Y-%m-%d %H:%M:%S")
                        if record.end_time
                        else "-"
                    ),
                    "duration": (
                        f"{record.duration:.1f}分钟" if record.duration else "-"
                    ),
                    "status": record.status,
                }
                for record in usage_records
            ],
        )

    except Exception as e:
        show_error(f"加载设备详情页面失败: {str(e)}")


@page_layout(title="设备组管理")
@require_auth
async def device_group_page() -> None:
    """设备组管理页面"""
    try:
        service = DeviceService()

        # 获取设备组列表
        groups = await service.get_groups()

        # 创建设备组表格
        create_crud_table(
            model="设备组",
            headers=["ID", "名称", "描述", "设备数量", "创建时间"],
            data=[
                {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "device_count": len(group.devices),
                    "created_at": group.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for group in groups
            ],
            create_form={
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "label": "组名称",
                        "required": True,
                    },
                    {"name": "description", "type": "textarea", "label": "组描述"},
                ],
                "on_create": service.create_group,
            },
            edit_form={
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "label": "组名称",
                        "required": True,
                    },
                    {"name": "description", "type": "textarea", "label": "组描述"},
                ],
                "get_data": service.get_group,
                "on_edit": service.update_group,
            },
        )

    except Exception as e:
        show_error(f"加载设备组管理页面失败: {str(e)}")


@page_layout(title="从服务器管理")
@require_auth
async def slave_server_page() -> None:
    """从服务器管理页面"""
    try:
        service = DeviceService()

        # 获取从服务器列表
        slaves = await service.get_slave_servers()

        # 获取从服务器状态统计
        stats = await service.get_slave_server_stats()

        # 创建仪表板
        create_dashboard(
            charts=[
                {
                    "type": "gauge",
                    "title": "从服务器在线率",
                    "value": stats["online_rate"],
                },
                {
                    "type": "pie",
                    "title": "从服务器状态分布",
                    "data": [
                        {"name": "在线", "value": stats["online_count"]},
                        {"name": "离线", "value": stats["offline_count"]},
                        {"name": "故障", "value": stats["error_count"]},
                    ],
                    "name_field": "name",
                    "value_field": "value",
                },
            ]
        )

        # 创建从服务器表格
        create_crud_table(
            model="从服务器",
            headers=["ID", "主机", "端口", "状态", "设备数量", "最后心跳时间"],
            data=[
                {
                    "id": slave.id,
                    "host": slave.host,
                    "port": slave.port,
                    "status": slave.status,
                    "device_count": len(slave.devices),
                    "last_heartbeat": (
                        slave.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
                        if slave.last_heartbeat
                        else "-"
                    ),
                }
                for slave in slaves
            ],
            create_form={
                "fields": [
                    {
                        "name": "host",
                        "type": "text",
                        "label": "主机地址",
                        "required": True,
                    },
                    {
                        "name": "port",
                        "type": "number",
                        "label": "端口号",
                        "required": True,
                    },
                ],
                "on_create": service.create_slave_server,
            },
            edit_form={
                "fields": [
                    {
                        "name": "host",
                        "type": "text",
                        "label": "主机地址",
                        "required": True,
                    },
                    {
                        "name": "port",
                        "type": "number",
                        "label": "端口号",
                        "required": True,
                    },
                ],
                "get_data": service.get_slave_server,
                "on_edit": service.update_slave_server,
            },
        )

    except Exception as e:
        show_error(f"加载从服务器管理页面失败: {str(e)}")
