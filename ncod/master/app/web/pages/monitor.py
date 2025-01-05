"""
监控页面
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from pywebio.output import put_html, put_loading
from pywebio.pin import pin

from ...core.auth import require_auth
from ...services.monitor import MonitorService
from ..components.chart import create_dashboard
from ..components.layout import page_layout
from ..components.notification import show_error
from ..components.table import create_crud_table


@page_layout(title="系统监控")
@require_auth
async def monitor_page() -> None:
    """系统监控页面"""
    try:
        service = MonitorService()

        # 获取系统状态
        status = await service.get_system_status()

        # 创建系统状态仪表板
        create_dashboard(
            charts=[
                {
                    "type": "gauge",
                    "title": "CPU使用率",
                    "value": status["cpu_usage"],
                    "min_value": 0,
                    "max_value": 100,
                },
                {
                    "type": "gauge",
                    "title": "内存使用率",
                    "value": status["memory_usage"],
                    "min_value": 0,
                    "max_value": 100,
                },
                {
                    "type": "gauge",
                    "title": "磁盘使用率",
                    "value": status["disk_usage"],
                    "min_value": 0,
                    "max_value": 100,
                },
            ]
        )

        # 获取性能指标
        metrics = await service.get_performance_metrics()

        # 创建性能指标图表
        create_dashboard(
            charts=[
                {
                    "type": "line",
                    "title": "CPU使用率趋势",
                    "data": metrics["cpu_trend"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "line",
                    "title": "内存使用率趋势",
                    "data": metrics["memory_trend"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "line",
                    "title": "网络流量趋势",
                    "data": metrics["network_trend"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "line",
                    "title": "磁盘IO趋势",
                    "data": metrics["disk_io_trend"],
                    "x_field": "time",
                    "y_field": "value",
                },
            ]
        )

    except Exception as e:
        show_error(f"加载系统监控页面失败: {str(e)}")


@page_layout(title="告警管理")
@require_auth
async def alert_page() -> None:
    """告警管理页面"""
    try:
        service = MonitorService()

        # 获取告警统计
        stats = await service.get_alert_stats()

        # 创建告警统计图表
        create_dashboard(
            charts=[
                {
                    "type": "pie",
                    "title": "告警级别分布",
                    "data": [
                        {"name": "严重", "value": stats["critical_count"]},
                        {"name": "警告", "value": stats["warning_count"]},
                        {"name": "信息", "value": stats["info_count"]},
                    ],
                    "name_field": "name",
                    "value_field": "value",
                },
                {
                    "type": "bar",
                    "title": "告警类型分布",
                    "data": stats["type_distribution"],
                    "x_field": "type",
                    "y_field": "count",
                },
            ]
        )

        # 获取告警列表
        alerts = await service.get_alerts()

        # 创建告警表格
        create_crud_table(
            model="告警",
            headers=["ID", "类型", "级别", "消息", "状态", "创建时间", "更新时间"],
            data=[
                {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "status": alert.status,
                    "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": alert.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for alert in alerts
            ],
        )

    except Exception as e:
        show_error(f"加载告警管理页面失败: {str(e)}")


@page_layout(title="性能分析")
@require_auth
async def performance_page() -> None:
    """性能分析页面"""
    try:
        service = MonitorService()

        # 获取性能数据
        performance_data = await service.get_performance_data()

        # 创建性能分析图表
        create_dashboard(
            charts=[
                {
                    "type": "line",
                    "title": "请求响应时间趋势",
                    "data": performance_data["response_time_trend"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "line",
                    "title": "并发请求数趋势",
                    "data": performance_data["concurrent_requests_trend"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "bar",
                    "title": "接口调用次数统计",
                    "data": performance_data["api_calls_stats"],
                    "x_field": "api",
                    "y_field": "count",
                },
                {
                    "type": "bar",
                    "title": "错误率统计",
                    "data": performance_data["error_rate_stats"],
                    "x_field": "api",
                    "y_field": "rate",
                },
            ]
        )

        # 获取性能问题列表
        issues = await service.get_performance_issues()

        # 创建性能问题表格
        create_crud_table(
            model="性能问题",
            headers=["ID", "类型", "描述", "影响", "建议", "发现时间"],
            data=[
                {
                    "id": issue.id,
                    "type": issue.issue_type,
                    "description": issue.description,
                    "impact": issue.impact,
                    "suggestion": issue.suggestion,
                    "found_at": issue.found_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for issue in issues
            ],
        )

    except Exception as e:
        show_error(f"加载性能分析页面失败: {str(e)}")


@page_layout(title="日志分析")
@require_auth
async def log_page() -> None:
    """日志分析页面"""
    try:
        service = MonitorService()

        # 获取日志统计
        stats = await service.get_log_stats()

        # 创建日志统计图表
        create_dashboard(
            charts=[
                {
                    "type": "pie",
                    "title": "日志级别分布",
                    "data": [
                        {"name": "ERROR", "value": stats["error_count"]},
                        {"name": "WARNING", "value": stats["warning_count"]},
                        {"name": "INFO", "value": stats["info_count"]},
                        {"name": "DEBUG", "value": stats["debug_count"]},
                    ],
                    "name_field": "name",
                    "value_field": "value",
                },
                {
                    "type": "line",
                    "title": "日志数量趋势",
                    "data": stats["log_trend"],
                    "x_field": "time",
                    "y_field": "count",
                },
            ]
        )

        # 获取日志列表
        logs = await service.get_logs()

        # 创建日志表格
        create_crud_table(
            model="日志",
            headers=["ID", "级别", "模块", "消息", "时间"],
            data=[
                {
                    "id": log.id,
                    "level": log.level,
                    "module": log.module,
                    "message": log.message,
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for log in logs
            ],
        )

    except Exception as e:
        show_error(f"加载日志分析页面失败: {str(e)}")


@page_layout(title="资源监控")
@require_auth
async def resource_page() -> None:
    """资源监控页面"""
    try:
        service = MonitorService()

        # 获取资源使用统计
        stats = await service.get_resource_stats()

        # 创建资源使用图表
        create_dashboard(
            charts=[
                {
                    "type": "line",
                    "title": "CPU核心使用率",
                    "data": stats["cpu_cores_usage"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "line",
                    "title": "内存使用详情",
                    "data": stats["memory_details"],
                    "x_field": "time",
                    "y_field": "value",
                },
                {
                    "type": "bar",
                    "title": "磁盘空间使用",
                    "data": stats["disk_usage"],
                    "x_field": "mount_point",
                    "y_field": "usage",
                },
                {
                    "type": "line",
                    "title": "网络带宽使用",
                    "data": stats["network_bandwidth"],
                    "x_field": "time",
                    "y_field": "value",
                },
            ]
        )

        # 获取进程列表
        processes = await service.get_processes()

        # 创建进程表格
        create_crud_table(
            model="进程",
            headers=["PID", "名称", "CPU使用率", "内存使用率", "状态", "启动时间"],
            data=[
                {
                    "id": process.pid,
                    "name": process.name,
                    "cpu_percent": f"{process.cpu_percent:.1f}%",
                    "memory_percent": f"{process.memory_percent:.1f}%",
                    "status": process.status,
                    "start_time": datetime.fromtimestamp(process.create_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
                for process in processes
            ],
        )

    except Exception as e:
        show_error(f"加载资源监控页面失败: {str(e)}")
