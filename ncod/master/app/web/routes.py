"""
Web路由
"""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from ncod.common.services.device import DeviceService
from ncod.common.services.monitor import MonitorService
from ncod.core.auth import require_auth
from ncod.core.log import Logger

logger = Logger(__name__)
monitor_service = MonitorService()
device_service = DeviceService()

# 创建蓝图
web_bp = Blueprint("web", __name__, url_prefix="/web")


@web_bp.route("/")
@require_auth
def index():
    """首页"""
    return render_template("index.html")


@web_bp.route("/dashboard")
@require_auth
def dashboard():
    """仪表盘"""
    # 获取系统指标
    metrics = monitor_service.collect_metrics()

    # 获取告警
    alerts = monitor_service.check_alerts()

    # 获取设备列表
    devices = device_service.get_devices()

    return render_template(
        "dashboard.html", metrics=metrics, alerts=alerts, devices=devices
    )


@web_bp.route("/devices")
@require_auth
def devices():
    """设备管理"""
    # 获取设备列表
    devices = device_service.get_devices()

    # 获取设备组列表
    groups = device_service.get_groups()

    return render_template("devices.html", devices=devices, groups=groups)


@web_bp.route("/devices/<int:device_id>")
@require_auth
def device_detail(device_id: int):
    """设备详情"""
    # 获取设备信息
    device = device_service.get_device(device_id)
    if not device:
        return redirect(url_for("web.devices"))

    # 获取设备监控指标
    metrics = monitor_service.get_device_metrics(device_id)

    # 获取设备告警
    alerts = monitor_service.get_device_alerts(device_id)

    return render_template(
        "device_detail.html", device=device, metrics=metrics, alerts=alerts
    )


@web_bp.route("/devices/<int:device_id>/metrics")
@require_auth
def device_metrics(device_id: int):
    """设备监控指标"""
    metrics = monitor_service.get_device_metrics(device_id)
    return jsonify(metrics)


@web_bp.route("/devices/<int:device_id>/alerts")
@require_auth
def device_alerts(device_id: int):
    """设备告警"""
    alerts = monitor_service.get_device_alerts(device_id)
    return jsonify(alerts)


@web_bp.route("/monitor")
@require_auth
def monitor():
    """监控中心"""
    # 获取系统指标
    metrics = monitor_service.collect_metrics()

    # 获取告警
    alerts = monitor_service.check_alerts()

    return render_template("monitor.html", metrics=metrics, alerts=alerts)


@web_bp.route("/monitor/metrics")
@require_auth
def monitor_metrics():
    """系统监控指标"""
    metrics = monitor_service.collect_metrics()
    return jsonify(metrics)


@web_bp.route("/monitor/alerts")
@require_auth
def monitor_alerts():
    """系统告警"""
    alerts = monitor_service.check_alerts()
    return jsonify(alerts)
