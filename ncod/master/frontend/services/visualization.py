"""Visualization模块"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
from database import db_manager
from models.user import Alert, Device, DeviceGroup, DeviceMetric
from services.cache import cache

logger = logging.getLogger(__name__)


class VisualizationService:
    """可视化服务"""

    @staticmethod
    async def generate_topology(group_id: Optional[int] = None) -> Dict[str, Any]:
        """生成设备拓扑图"""
        try:
            with db_manager.get_session() as session:
                # 创建图
                G = nx.Graph()

                # 获取设备列表
                query = session.query(Device)
                if group_id:
                    group = session.query(DeviceGroup).get(group_id)
                    if group:
                        devices = group.devices
                    else:
                        return {}
                else:
                    devices = query.all()

                # 添加节点
                for device in devices:
                    G.add_node(
                        device.id,
                        name=device.name,
                        type=device.type,
                        subtype=device.subtype,
                        status=device.status,
                    )

                # 添加连接关系（根据设备配置中的连接信息）
                for device in devices:
                    connections = device.config.get("connections", [])
                    for conn in connections:
                        if conn["target_id"] in [d.id for d in devices]:
                            G.add_edge(
                                device.id,
                                conn["target_id"],
                                type=conn.get("type", "link"),
                            )

                # 使用spring_layout布局
                pos = nx.spring_layout(G)

                # 创建节点跟踪
                node_trace = go.Scatter(
                    x=[pos[node][0] for node in G.nodes()],
                    y=[pos[node][1] for node in G.nodes()],
                    mode="markers+text",
                    hoverinfo="text",
                    text=[
                        f"{G.nodes[node]['name']}<br>{G.nodes[node]['type']}"
                        for node in G.nodes()
                    ],
                    marker=dict(
                        size=20,
                        color=[
                            (
                                "green"
                                if G.nodes[node]["status"] == "online"
                                else (
                                    "red"
                                    if G.nodes[node]["status"] == "error"
                                    else "gray"
                                )
                            )
                            for node in G.nodes()
                        ],
                    ),
                )

                # 创建边跟踪
                edge_trace = go.Scatter(
                    x=[pos[edge[0]][0] for edge in G.edges()]
                    + [pos[edge[1]][0] for edge in G.edges()],
                    y=[pos[edge[0]][1] for edge in G.edges()]
                    + [pos[edge[1]][1] for edge in G.edges()],
                    mode="lines",
                    line=dict(width=1, color="#888"),
                    hoverinfo="none",
                )

                # 创建图形
                fig = go.Figure(
                    data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode="closest",
                        margin=dict(b=0, l=0, r=0, t=0),
                    ),
                )

                return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"Failed to generate topology: {e}")
            return {}

    @staticmethod
    async def generate_performance_trends(
        device_id: int, metric_type: str, time_range: str = "24h"
    ) -> Dict[str, Any]:
        """生成性能趋势图"""
        try:
            with db_manager.get_session() as session:
                # 计算时间范围
                end_time = datetime.utcnow()
                if time_range == "24h":
                    start_time = end_time - timedelta(hours=24)
                elif time_range == "7d":
                    start_time = end_time - timedelta(days=7)
                elif time_range == "30d":
                    start_time = end_time - timedelta(days=30)
                else:
                    start_time = end_time - timedelta(hours=24)

                # 获取指标数据
                metrics = (
                    session.query(DeviceMetric)
                    .filter(
                        DeviceMetric.device_id == device_id,
                        DeviceMetric.metric_type == metric_type,
                        DeviceMetric.collected_at.between(start_time, end_time),
                    )
                    .order_by(DeviceMetric.collected_at.asc())
                    .all()
                )

                if not metrics:
                    return {}

                # 创建趋势图
                fig = go.Figure()

                # 添加指标线
                fig.add_trace(
                    go.Scatter(
                        x=[m.collected_at for m in metrics],
                        y=[float(m.value) for m in metrics],
                        mode="lines+markers",
                        name=metrics[0].metric_name,
                        hovertemplate="%{y:.2f} " + metrics[0].unit,
                    )
                )

                # 添加阈值线（如果有配置）
                device = session.query(Device).get(device_id)
                if device and device.monitoring_config:
                    thresholds = device.monitoring_config.get("thresholds", {})
                    if metric_type in thresholds:
                        threshold = thresholds[metric_type]
                        fig.add_hline(
                            y=threshold["value"],
                            line_dash="dash",
                            line_color="red",
                            annotation_text=f"Threshold: {threshold['value']}",
                        )

                # 更新布局
                fig.update_layout(
                    title=f"{metric_type.title()} Trend",
                    xaxis_title="Time",
                    yaxis_title=metrics[0].unit,
                    hovermode="x unified",
                )

                return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"Failed to generate performance trends: {e}")
            return {}

    @staticmethod
    async def generate_alert_statistics(time_range: str = "24h") -> Dict[str, Any]:
        """生成告警统计图"""
        try:
            with db_manager.get_session() as session:
                # 计算时间范围
                end_time = datetime.utcnow()
                if time_range == "24h":
                    start_time = end_time - timedelta(hours=24)
                elif time_range == "7d":
                    start_time = end_time - timedelta(days=7)
                elif time_range == "30d":
                    start_time = end_time - timedelta(days=30)
                else:
                    start_time = end_time - timedelta(hours=24)

                # 获取告警数据
                alerts = (
                    session.query(Alert)
                    .filter(Alert.created_at.between(start_time, end_time))
                    .all()
                )

                if not alerts:
                    return {}

                # 按严重程度统计
                severity_stats = {}
                for alert in alerts:
                    severity_stats[alert.severity] = (
                        severity_stats.get(alert.severity, 0) + 1
                    )

                # 创建饼图
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=list(severity_stats.keys()),
                            values=list(severity_stats.values()),
                            hole=0.3,
                            marker_colors=["red", "orange", "yellow", "blue"],
                        )
                    ]
                )

                # 更新布局
                fig.update_layout(
                    title="Alert Statistics by Severity",
                    annotations=[
                        dict(text="Alerts", x=0.5, y=0.5, font_size=20, showarrow=False)
                    ],
                )

                return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"Failed to generate alert statistics: {e}")
            return {}

    @staticmethod
    async def generate_resource_dashboard(device_id: int) -> Dict[str, Any]:
        """生成资源使用率仪表板"""
        try:
            with db_manager.get_session() as session:
                device = session.query(Device).get(device_id)
                if not device:
                    return {}

                # 获取最新的指标数据
                metrics = (
                    session.query(DeviceMetric)
                    .filter(
                        DeviceMetric.device_id == device_id,
                        DeviceMetric.collected_at
                        >= datetime.utcnow() - timedelta(minutes=5),
                    )
                    .all()
                )

                if not metrics:
                    return {}

                # 创建仪表板
                fig = go.Figure()

                # 添加CPU使用率仪表
                cpu_metric = next((m for m in metrics if m.metric_type == "cpu"), None)
                if cpu_metric:
                    fig.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=float(cpu_metric.value),
                            domain={"x": [0, 0.3], "y": [0, 1]},
                            title={"text": "CPU Usage"},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar": {"color": "darkblue"},
                                "steps": [
                                    {"range": [0, 50], "color": "lightgray"},
                                    {"range": [50, 80], "color": "gray"},
                                    {"range": [80, 100], "color": "red"},
                                ],
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": 90,
                                },
                            },
                        )
                    )

                # 添加内存使用率仪表
                memory_metric = next(
                    (m for m in metrics if m.metric_type == "memory"), None
                )
                if memory_metric:
                    fig.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=float(memory_metric.value),
                            domain={"x": [0.35, 0.65], "y": [0, 1]},
                            title={"text": "Memory Usage"},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar": {"color": "darkblue"},
                                "steps": [
                                    {"range": [0, 50], "color": "lightgray"},
                                    {"range": [50, 80], "color": "gray"},
                                    {"range": [80, 100], "color": "red"},
                                ],
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": 90,
                                },
                            },
                        )
                    )

                # 添加磁盘使用率仪表
                disk_metric = next(
                    (m for m in metrics if m.metric_type == "disk"), None
                )
                if disk_metric:
                    fig.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=float(disk_metric.value),
                            domain={"x": [0.7, 1], "y": [0, 1]},
                            title={"text": "Disk Usage"},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar": {"color": "darkblue"},
                                "steps": [
                                    {"range": [0, 50], "color": "lightgray"},
                                    {"range": [50, 80], "color": "gray"},
                                    {"range": [80, 100], "color": "red"},
                                ],
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": 90,
                                },
                            },
                        )
                    )

                # 更新布局
                fig.update_layout(
                    title=f"Resource Usage Dashboard - {device.name}",
                    grid={"rows": 1, "columns": 3, "pattern": "independent"},
                )

                return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"Failed to generate resource dashboard: {e}")
            return {}

    @staticmethod
    async def generate_geo_map(devices: List[Device]) -> Dict[str, Any]:
        """生成设备地理位置分布图"""
        try:
            # 创建地图
            fig = go.Figure()

            # 添加设备标记
            lats = []
            lons = []
            texts = []
            colors = []

            for device in devices:
                if (
                    device.location
                    and "latitude" in device.location
                    and "longitude" in device.location
                ):
                    lats.append(device.location["latitude"])
                    lons.append(device.location["longitude"])
                    texts.append(f"{device.name}<br>{device.type}")
                    colors.append(
                        "green"
                        if device.status == "online"
                        else "red" if device.status == "error" else "gray"
                    )

            if lats and lons:
                fig.add_trace(
                    go.Scattergeo(
                        lon=lons,
                        lat=lats,
                        text=texts,
                        mode="markers",
                        marker=dict(
                            size=10, color=colors, line=dict(width=1, color="black")
                        ),
                    )
                )

                # 更新布局
                fig.update_layout(
                    title="Device Geographic Distribution",
                    geo=dict(
                        showland=True,
                        showcountries=True,
                        showocean=True,
                        countrywidth=0.5,
                        landcolor="rgb(243, 243, 243)",
                        oceancolor="rgb(204, 229, 255)",
                        projection_scale=1.2,
                    ),
                    showlegend=False,
                )

                return json.loads(fig.to_json())

            return {}

        except Exception as e:
            logger.error(f"Failed to generate geo map: {e}")
            return {}

    @staticmethod
    async def generate_service_dependency(devices: List[Device]) -> Dict[str, Any]:
        """生成服务依赖关系图"""
        try:
            # 创建有向图
            G = nx.DiGraph()

            # 添加节点和边
            for device in devices:
                G.add_node(
                    device.id, name=device.name, type=device.type, status=device.status
                )

                # 添加依赖关系
                dependencies = device.config.get("dependencies", [])
                for dep in dependencies:
                    if dep["target_id"] in [d.id for d in devices]:
                        G.add_edge(
                            device.id,
                            dep["target_id"],
                            type=dep.get("type", "depends_on"),
                        )

            # 使用spring_layout布局
            pos = nx.spring_layout(G)

            # 创建节点跟踪
            node_trace = go.Scatter(
                x=[pos[node][0] for node in G.nodes()],
                y=[pos[node][1] for node in G.nodes()],
                mode="markers+text",
                hoverinfo="text",
                text=[
                    f"{G.nodes[node]['name']}<br>{G.nodes[node]['type']}"
                    for node in G.nodes()
                ],
                marker=dict(
                    size=20,
                    color=[
                        (
                            "green"
                            if G.nodes[node]["status"] == "online"
                            else "red" if G.nodes[node]["status"] == "error" else "gray"
                        )
                        for node in G.nodes()
                    ],
                ),
            )

            # 创建边跟踪
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line=dict(width=1, color="#888"),
                hoverinfo="none",
            )

            # 创建图形
            fig = go.Figure(
                data=[edge_trace, node_trace],
                layout=go.Layout(
                    title="Service Dependencies",
                    showlegend=False,
                    hovermode="closest",
                    margin=dict(b=20, l=5, r=5, t=40),
                ),
            )

            return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"Failed to generate service dependency: {e}")
            return {}

    @staticmethod
    async def generate_performance_heatmap(
        device_id: int, metric_type: str, days: int = 7
    ) -> Dict[str, Any]:
        """生成性能热力图"""
        try:
            with db_manager.get_session() as session:
                # 获取时间范围内的指标数据
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=days)

                metrics = (
                    session.query(DeviceMetric)
                    .filter(
                        DeviceMetric.device_id == device_id,
                        DeviceMetric.metric_type == metric_type,
                        DeviceMetric.collected_at.between(start_time, end_time),
                    )
                    .order_by(DeviceMetric.collected_at.asc())
                    .all()
                )

                if not metrics:
                    return {}

                # 准备热力图数据
                dates = []
                hours = []
                values = []

                for metric in metrics:
                    date = metric.collected_at.strftime("%Y-%m-%d")
                    hour = metric.collected_at.hour
                    value = float(metric.value)

                    dates.append(date)
                    hours.append(hour)
                    values.append(value)

                # 创建热力图
                fig = go.Figure(
                    data=go.Heatmap(x=dates, y=hours, z=values, colorscale="Viridis")
                )

                # 更新布局
                fig.update_layout(
                    title=f"{metric_type.title()} Performance Heatmap",
                    xaxis_title="Date",
                    yaxis_title="Hour",
                    yaxis=dict(
                        ticktext=[f"{h:02d}:00" for h in range(24)],
                        tickvals=list(range(24)),
                    ),
                )

                return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"Failed to generate performance heatmap: {e}")
            return {}

    @staticmethod
    async def generate_custom_dashboard(config: Dict[str, Any]) -> Dict[str, Any]:
        """生成自定义仪表板"""
        try:
            # 创建子图布局
            fig = make_subplots(
                rows=config.get("rows", 2),
                cols=config.get("cols", 2),
                subplot_titles=config.get("titles", []),
                specs=config.get(
                    "specs",
                    [[{"type": "xy"}] * config.get("cols", 2)] * config.get("rows", 2),
                ),
            )

            # 处理每个图表
            for chart in config.get("charts", []):
                try:
                    # 获取数据
                    with db_manager.get_session() as session:
                        if chart["type"] == "metric_trend":
                            # 指标趋势图
                            metrics = (
                                session.query(DeviceMetric)
                                .filter(
                                    DeviceMetric.device_id == chart["device_id"],
                                    DeviceMetric.metric_type == chart["metric_type"],
                                    DeviceMetric.collected_at
                                    >= datetime.utcnow()
                                    - timedelta(hours=chart.get("hours", 24)),
                                )
                                .order_by(DeviceMetric.collected_at.asc())
                                .all()
                            )

                            fig.add_trace(
                                go.Scatter(
                                    x=[m.collected_at for m in metrics],
                                    y=[float(m.value) for m in metrics],
                                    name=chart["title"],
                                ),
                                row=chart["row"],
                                col=chart["col"],
                            )

                        elif chart["type"] == "alert_pie":
                            # 告警饼图
                            alerts = (
                                session.query(Alert)
                                .filter(
                                    Alert.created_at
                                    >= datetime.utcnow()
                                    - timedelta(hours=chart.get("hours", 24))
                                )
                                .all()
                            )

                            severity_stats = {}
                            for alert in alerts:
                                severity_stats[alert.severity] = (
                                    severity_stats.get(alert.severity, 0) + 1
                                )

                            fig.add_trace(
                                go.Pie(
                                    labels=list(severity_stats.keys()),
                                    values=list(severity_stats.values()),
                                    name=chart["title"],
                                ),
                                row=chart["row"],
                                col=chart["col"],
                            )

                        elif chart["type"] == "device_status":
                            # 设备状态统计
                            devices = session.query(Device).all()
                            status_stats = {}
                            for device in devices:
                                status_stats[device.status] = (
                                    status_stats.get(device.status, 0) + 1
                                )

                            fig.add_trace(
                                go.Bar(
                                    x=list(status_stats.keys()),
                                    y=list(status_stats.values()),
                                    name=chart["title"],
                                ),
                                row=chart["row"],
                                col=chart["col"],
                            )

                except Exception as e:
                    logger.error(f"Failed to generate chart: {e}")

            # 更新布局
            fig.update_layout(
                title=config.get("title", "Custom Dashboard"),
                showlegend=True,
                height=config.get("height", 800),
            )

            return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"Failed to generate custom dashboard: {e}")
            return {}


# 创建可视化服务实例
visualization_service = VisualizationService()
