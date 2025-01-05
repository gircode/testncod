"""
系统设置页面
"""

from typing import Any, Dict

from pywebio.output import put_html, put_loading
from pywebio.pin import pin

from ...core.auth import require_auth
from ...services.config import ConfigService
from ..components.form import create_form
from ..components.layout import page_layout
from ..components.notification import show_error, show_success


@page_layout(title="系统设置")
@require_auth
async def settings_page() -> None:
    """系统设置页面"""
    try:
        service = ConfigService()

        # 获取当前配置
        config = await service.get_config()

        # 创建系统设置表单
        create_form(
            fields=[
                {
                    "name": "system_name",
                    "type": "text",
                    "label": "系统名称",
                    "value": config.get("system_name"),
                    "required": True,
                },
                {
                    "name": "admin_email",
                    "type": "email",
                    "label": "管理员邮箱",
                    "value": config.get("admin_email"),
                    "required": True,
                },
                {
                    "name": "log_level",
                    "type": "select",
                    "label": "日志级别",
                    "value": config.get("log_level"),
                    "options": [
                        {"label": "DEBUG", "value": "debug"},
                        {"label": "INFO", "value": "info"},
                        {"label": "WARNING", "value": "warning"},
                        {"label": "ERROR", "value": "error"},
                    ],
                    "required": True,
                },
                {
                    "name": "metrics_retention_days",
                    "type": "number",
                    "label": "监控指标保留天数",
                    "value": config.get("metrics_retention_days"),
                    "required": True,
                },
                {
                    "name": "alert_retention_days",
                    "type": "number",
                    "label": "告警记录保留天数",
                    "value": config.get("alert_retention_days"),
                    "required": True,
                },
                {
                    "name": "usage_retention_days",
                    "type": "number",
                    "label": "使用记录保留天数",
                    "value": config.get("usage_retention_days"),
                    "required": True,
                },
                {
                    "name": "max_device_usage_hours",
                    "type": "number",
                    "label": "最大设备使用时长(小时)",
                    "value": config.get("max_device_usage_hours"),
                    "required": True,
                },
                {
                    "name": "monitor_interval",
                    "type": "number",
                    "label": "监控采集间隔(秒)",
                    "value": config.get("monitor_interval"),
                    "required": True,
                },
                {
                    "name": "alert_check_interval",
                    "type": "number",
                    "label": "告警检查间隔(秒)",
                    "value": config.get("alert_check_interval"),
                    "required": True,
                },
                {
                    "name": "slave_health_check_interval",
                    "type": "number",
                    "label": "从服务器健康检查间隔(秒)",
                    "value": config.get("slave_health_check_interval"),
                    "required": True,
                },
                {
                    "name": "device_check_interval",
                    "type": "number",
                    "label": "设备状态检查间隔(秒)",
                    "value": config.get("device_check_interval"),
                    "required": True,
                },
                {
                    "name": "request_timeout",
                    "type": "number",
                    "label": "请求超时时间(秒)",
                    "value": config.get("request_timeout"),
                    "required": True,
                },
            ],
            on_submit=handle_settings_submit,
            submit_text="保存设置",
        )

    except Exception as e:
        show_error(f"加载系统设置页面失败: {str(e)}")


async def handle_settings_submit(data: Dict[str, Any]) -> None:
    """处理系统设置提交

    Args:
        data: 表单数据
    """
    try:
        service = ConfigService()

        # 更新配置
        await service.update_config(data)

        show_success("系统设置已更新")

    except Exception as e:
        show_error(f"更新系统设置失败: {str(e)}")


@page_layout(title="邮件设置")
@require_auth
async def email_settings_page() -> None:
    """邮件设置页面"""
    try:
        service = ConfigService()

        # 获取当前邮件配置
        config = await service.get_email_config()

        # 创建邮件设置表单
        create_form(
            fields=[
                {
                    "name": "smtp_server",
                    "type": "text",
                    "label": "SMTP服务器",
                    "value": config.get("smtp_server"),
                    "required": True,
                },
                {
                    "name": "smtp_port",
                    "type": "number",
                    "label": "SMTP端口",
                    "value": config.get("smtp_port"),
                    "required": True,
                },
                {
                    "name": "smtp_username",
                    "type": "text",
                    "label": "SMTP用户名",
                    "value": config.get("smtp_username"),
                    "required": True,
                },
                {
                    "name": "smtp_password",
                    "type": "password",
                    "label": "SMTP密码",
                    "value": config.get("smtp_password"),
                    "required": True,
                },
                {
                    "name": "sender_email",
                    "type": "email",
                    "label": "发件人邮箱",
                    "value": config.get("sender_email"),
                    "required": True,
                },
                {
                    "name": "sender_name",
                    "type": "text",
                    "label": "发件人名称",
                    "value": config.get("sender_name"),
                    "required": True,
                },
            ],
            on_submit=handle_email_settings_submit,
            submit_text="保存设置",
        )

    except Exception as e:
        show_error(f"加载邮件设置页面失败: {str(e)}")


async def handle_email_settings_submit(data: Dict[str, Any]) -> None:
    """处理邮件设置提交

    Args:
        data: 表单数据
    """
    try:
        service = ConfigService()

        # 更新邮件配置
        await service.update_email_config(data)

        show_success("邮件设置已更新")

    except Exception as e:
        show_error(f"更新邮件设置失败: {str(e)}")


@page_layout(title="备份设置")
@require_auth
async def backup_settings_page() -> None:
    """备份设置页面"""
    try:
        service = ConfigService()

        # 获取当前备份配置
        config = await service.get_backup_config()

        # 创建备份设置表单
        create_form(
            fields=[
                {
                    "name": "backup_enabled",
                    "type": "checkbox",
                    "label": "启用自动备份",
                    "value": config.get("backup_enabled"),
                    "required": True,
                },
                {
                    "name": "backup_interval",
                    "type": "number",
                    "label": "备份间隔(小时)",
                    "value": config.get("backup_interval"),
                    "required": True,
                },
                {
                    "name": "backup_retention_days",
                    "type": "number",
                    "label": "备份保留天数",
                    "value": config.get("backup_retention_days"),
                    "required": True,
                },
                {
                    "name": "backup_path",
                    "type": "text",
                    "label": "备份路径",
                    "value": config.get("backup_path"),
                    "required": True,
                },
                {
                    "name": "backup_compress",
                    "type": "checkbox",
                    "label": "启用压缩",
                    "value": config.get("backup_compress"),
                },
                {
                    "name": "backup_encrypt",
                    "type": "checkbox",
                    "label": "启用加密",
                    "value": config.get("backup_encrypt"),
                },
            ],
            on_submit=handle_backup_settings_submit,
            submit_text="保存设置",
        )

    except Exception as e:
        show_error(f"加载备份设置页面失败: {str(e)}")


async def handle_backup_settings_submit(data: Dict[str, Any]) -> None:
    """处理备份设置提交

    Args:
        data: 表单数据
    """
    try:
        service = ConfigService()

        # 更新备份配置
        await service.update_backup_config(data)

        show_success("备份设置已更新")

    except Exception as e:
        show_error(f"更新备份设置失败: {str(e)}")


@page_layout(title="安全设置")
@require_auth
async def security_settings_page() -> None:
    """安全设置页面"""
    try:
        service = ConfigService()

        # 获取当前安全配置
        config = await service.get_security_config()

        # 创建安全设置表单
        create_form(
            fields=[
                {
                    "name": "password_min_length",
                    "type": "number",
                    "label": "密码最小长度",
                    "value": config.get("password_min_length"),
                    "required": True,
                },
                {
                    "name": "password_complexity",
                    "type": "select",
                    "label": "密码复杂度要求",
                    "value": config.get("password_complexity"),
                    "options": [
                        {"label": "低", "value": "low"},
                        {"label": "中", "value": "medium"},
                        {"label": "高", "value": "high"},
                    ],
                    "required": True,
                },
                {
                    "name": "password_expire_days",
                    "type": "number",
                    "label": "密码过期天数",
                    "value": config.get("password_expire_days"),
                    "required": True,
                },
                {
                    "name": "session_timeout",
                    "type": "number",
                    "label": "会话超时时间(分钟)",
                    "value": config.get("session_timeout"),
                    "required": True,
                },
                {
                    "name": "max_login_attempts",
                    "type": "number",
                    "label": "最大登录尝试次数",
                    "value": config.get("max_login_attempts"),
                    "required": True,
                },
                {
                    "name": "lockout_duration",
                    "type": "number",
                    "label": "账号锁定时长(分钟)",
                    "value": config.get("lockout_duration"),
                    "required": True,
                },
                {
                    "name": "enable_2fa",
                    "type": "checkbox",
                    "label": "启用双因素认证",
                    "value": config.get("enable_2fa"),
                },
                {
                    "name": "enable_ip_whitelist",
                    "type": "checkbox",
                    "label": "启用IP白名单",
                    "value": config.get("enable_ip_whitelist"),
                },
                {
                    "name": "ip_whitelist",
                    "type": "textarea",
                    "label": "IP白名单(每行一个)",
                    "value": config.get("ip_whitelist"),
                },
            ],
            on_submit=handle_security_settings_submit,
            submit_text="保存设置",
        )

    except Exception as e:
        show_error(f"加载安全设置页面失败: {str(e)}")


async def handle_security_settings_submit(data: Dict[str, Any]) -> None:
    """处理安全设置提交

    Args:
        data: 表单数据
    """
    try:
        service = ConfigService()

        # 更新安全配置
        await service.update_security_config(data)

        show_success("安全设置已更新")

    except Exception as e:
        show_error(f"更新安全设置失败: {str(e)}")
