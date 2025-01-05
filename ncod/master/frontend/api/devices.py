"""
设备API函数
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings


async def get_device_metrics(
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """获取设备指标"""
    params = {}
    if device_id:
        params["device_id"] = device_id
    if start_time:
        params["start_time"] = start_time.isoformat()
    if end_time:
        params["end_time"] = end_time.isoformat()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.API_URL}/api/v1/devices/metrics", params=params
        )
        response.raise_for_status()
        return response.json()


async def get_device_status(device_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取设备状态"""
    params = {}
    if device_id:
        params["device_id"] = device_id

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.API_URL}/api/v1/devices/status", params=params
        )
        response.raise_for_status()
        return response.json()


async def get_device_alerts(
    device_id: Optional[str] = None,
    severity: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """获取设备告警"""
    params = {}
    if device_id:
        params["device_id"] = device_id
    if severity:
        params["severity"] = severity
    if start_time:
        params["start_time"] = start_time.isoformat()
    if end_time:
        params["end_time"] = end_time.isoformat()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.API_URL}/api/v1/devices/alerts", params=params
        )
        response.raise_for_status()
        return response.json()


async def get_device_trends(
    device_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    interval: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """获取设备趋势"""
    params = {}
    if device_id:
        params["device_id"] = device_id
    if metric_type:
        params["metric_type"] = metric_type
    if interval:
        params["interval"] = interval
    if start_time:
        params["start_time"] = start_time.isoformat()
    if end_time:
        params["end_time"] = end_time.isoformat()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.API_URL}/api/v1/devices/trends", params=params
        )
        response.raise_for_status()
        return response.json()
