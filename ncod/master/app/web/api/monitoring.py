"""Monitoring模块"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ...config.config_manager import config_manager
from ...core.exceptions import ConfigError, ValidationError
from ...monitoring.metrics_collector import metrics_collector

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics/dashboard")
async def get_dashboard_metrics(time_range: str = "1h"):
    """获取仪表板指标数据"""
    try:
        # 解析时间范围
        end_time = datetime.now()
        start_time = end_time - parse_time_range(time_range)

        # 获取指标数据
        metrics = await metrics_collector.get_metrics(start_time, end_time)

        # 格式化数据
        return {
            "system_metrics": format_system_metrics(metrics),
            "performance_metrics": format_performance_metrics(metrics),
            "error_metrics": format_error_metrics(metrics),
        }
    except Exception as e:
        logger.error(f"获取仪表板指标数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    """获取所有指标数据"""
    try:
        metrics = await metrics_collector.get_all_metrics()
        return format_metrics_list(metrics)
    except Exception as e:
        logger.error(f"获取指标数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/export")
async def export_metrics():
    """导出指标数据"""
    try:
        metrics = await metrics_collector.get_all_metrics()

        # 创建临时文件
        filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join("/tmp", filename)

        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)

        return FileResponse(filepath, media_type="application/json", filename=filename)
    except Exception as e:
        logger.error(f"导出指标数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/import")
async def import_metrics(file: UploadFile = File(...)):
    """导入指标数据"""
    try:
        content = await file.read()
        metrics = json.loads(content)

        # 验证数据格式
        if not isinstance(metrics, list):
            raise ValidationError("无效的指标数据格式")

        # 导入数据
        await metrics_collector.import_metrics(metrics)
        return {"message": "指标数据导入成功"}
    except Exception as e:
        logger.error(f"导入指标数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/rules")
async def get_alert_rules():
    """获取警报规则"""
    try:
        rules = await config_manager.get_alert_rules()
        return rules
    except Exception as e:
        logger.error(f"获取警报规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/rules")
async def create_alert_rule(rule: Dict[str, Any]):
    """创建警报规则"""
    try:
        await config_manager.add_alert_rule(rule)
        return {"message": "警报规则创建成功"}
    except Exception as e:
        logger.error(f"创建警报规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/rules/{rule_id}")
async def get_alert_rule(rule_id: str):
    """获取警报规则详���"""
    try:
        rule = await config_manager.get_alert_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="警报规则不存在")
        return rule
    except Exception as e:
        logger.error(f"获取警报规则详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """删除警报规则"""
    try:
        await config_manager.delete_alert_rule(rule_id)
        return {"message": "警报规则删除成功"}
    except Exception as e:
        logger.error(f"删除警报规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/active")
async def get_active_alerts():
    """获取活动警报"""
    try:
        alerts = await metrics_collector.get_active_alerts()
        return format_alerts(alerts)
    except Exception as e:
        logger.error(f"获取活动警报失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """获取配置"""
    try:
        return {
            "monitoring": await config_manager.get_monitoring_config(),
            "alerts": await config_manager.get_alert_config(),
        }
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def save_config(config: Dict[str, Any]):
    """保存配置"""
    try:
        await config_manager.update_monitoring_config(config["monitoring"])
        await config_manager.update_alert_config(config["alerts"])
        return {"message": "配置保存成功"}
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/reload")
async def reload_config():
    """重新加载配置"""
    try:
        await config_manager.reload_config()
        return {"message": "配置重新加载成功"}
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def parse_time_range(time_range: str) -> timedelta:
    """解析时间范围"""
    unit = time_range[-1]
    value = int(time_range[:-1])

    if unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    else:
        raise ValidationError(f"无效的时间范围: {time_range}")


def format_system_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """格式化系统指标数据"""
    return {
        "cpu_usage": {
            "timestamps": [m["timestamp"] for m in metrics["cpu"]],
            "values": [m["value"] for m in metrics["cpu"]],
        },
        "memory_usage": {
            "timestamps": [m["timestamp"] for m in metrics["memory"]],
            "used": [m["used"] for m in metrics["memory"]],
            "available": [m["available"] for m in metrics["memory"]],
        },
        "disk_usage": {
            "used": metrics["disk"]["used"],
            "available": metrics["disk"]["available"],
        },
        "network_traffic": {
            "timestamps": [m["timestamp"] for m in metrics["network"]],
            "sent": [m["sent"] for m in metrics["network"]],
            "received": [m["received"] for m in metrics["network"]],
        },
    }


def format_performance_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """格式化性能指标数据"""
    return {
        "response_times": {
            "labels": metrics["response_times"]["labels"],
            "values": metrics["response_times"]["values"],
        },
        "request_counts": {
            "timestamps": [m["timestamp"] for m in metrics["requests"]],
            "values": [m["count"] for m in metrics["requests"]],
        },
    }


def format_error_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """格式化错误指标数据"""
    return {
        "error_types": {
            "labels": list(metrics["errors"]["by_type"].keys()),
            "values": list(metrics["errors"]["by_type"].values()),
        },
        "error_trend": {
            "timestamps": [m["timestamp"] for m in metrics["errors"]["trend"]],
            "values": [m["count"] for m in metrics["errors"]["trend"]],
        },
    }


def format_metrics_list(metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """格式化指标列表"""
    return [
        {
            "name": metric["name"],
            "type": metric["type"],
            "value": metric["value"],
            "timestamp": metric["timestamp"].isoformat(),
        }
        for metric in metrics
    ]


def format_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """格式化警报数据"""
    return [
        {
            "rule_name": alert["rule_name"],
            "message": alert["message"],
            "severity": alert["severity"],
            "timestamp": alert["timestamp"].isoformat(),
        }
        for alert in alerts
    ]
