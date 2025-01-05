"""设备仪表板页面"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ..api import get_device_metrics, get_device_status
from ..core.monitoring import PerformanceMonitor
from ..utils import apply_theme, format_bytes, format_duration, require_auth

# 初始化性能监控
performance_monitor = PerformanceMonitor()


class DeviceDashboard:
    def __init__(self):
        self.theme = apply_theme()

    @require_auth
    async def render(self):
        """渲染设备仪表板"""
        st.title("设备仪表板")

        # 刷新控制
        self._render_refresh_controls()

        try:
            # 设备概览
            await self._render_device_overview()

            # 设备状态
            await self._render_device_status()

            # 设备指标
            await self._render_device_metrics()

            # 告警摘要
            await self._render_alert_summary()

            # 趋势图表
            await self._render_trend_charts()

            # 性能指标
            self._show_performance_metrics()

        except Exception as e:
            st.error(f"加载仪表板失败: {str(e)}")
            performance_monitor.record_error()

    def _render_refresh_controls(self):
        """渲染刷新控制"""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("上次更新: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with col2:
            if st.button("刷新"):
                st.experimental_rerun()

    async def _render_device_overview(self):
        """渲染设备概览"""
        try:
            metrics = await get_device_metrics()

            cols = st.columns(4)

            cols[0].metric(
                "在线设备",
                str(metrics.get("online_count", 0)),
                delta=self._calculate_delta(
                    metrics.get("online_count", 0),
                    metrics.get("previous_online_count", 0),
                ),
            )

            cols[1].metric(
                "离线设备",
                str(metrics.get("offline_count", 0)),
                delta=self._calculate_delta(
                    metrics.get("offline_count", 0),
                    metrics.get("previous_offline_count", 0),
                ),
                delta_color="inverse",
            )

            cols[2].metric(
                "告警设备",
                str(metrics.get("alert_count", 0)),
                delta=self._calculate_delta(
                    metrics.get("alert_count", 0),
                    metrics.get("previous_alert_count", 0),
                ),
                delta_color="inverse",
            )

            cols[3].metric(
                "维护设备",
                str(metrics.get("maintenance_count", 0)),
                delta=self._calculate_delta(
                    metrics.get("maintenance_count", 0),
                    metrics.get("previous_maintenance_count", 0),
                ),
            )

        except Exception as e:
            st.error(f"获取设备概览失败: {str(e)}")
            performance_monitor.record_error()

    async def _render_device_status(self):
        """渲染设备状态"""
        try:
            status = await get_device_status()
            if not status:
                st.warning("暂无设备状态数据")
                return

            # 创建状态表格
            df = pd.DataFrame(status)
            st.dataframe(df)

        except Exception as e:
            st.error(f"获取设备状态失败: {str(e)}")
            performance_monitor.record_error()

    async def _render_device_metrics(self):
        """渲染设备指标"""
        try:
            metrics = await get_device_metrics()
            if not metrics:
                st.warning("暂无设备指标数据")
                return

            # 创建指标图表
            fig = make_subplots(rows=2, cols=2)

            # CPU使用率
            fig.add_trace(
                go.Scatter(
                    x=metrics.get("timestamps", []),
                    y=metrics.get("cpu_usage", []),
                    name="CPU使用率",
                ),
                row=1,
                col=1,
            )

            # 内存使用率
            fig.add_trace(
                go.Scatter(
                    x=metrics.get("timestamps", []),
                    y=metrics.get("memory_usage", []),
                    name="内存使用率",
                ),
                row=1,
                col=2,
            )

            # 网络流量
            fig.add_trace(
                go.Scatter(
                    x=metrics.get("timestamps", []),
                    y=metrics.get("network_in", []),
                    name="网络入流量",
                ),
                row=2,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=metrics.get("timestamps", []),
                    y=metrics.get("network_out", []),
                    name="网络出流量",
                ),
                row=2,
                col=2,
            )

            fig.update_layout(height=800)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"获取设备指标失败: {str(e)}")
            performance_monitor.record_error()

    async def _render_alert_summary(self):
        """渲染告警摘要"""
        try:
            alerts = await self._get_alerts()
            if not alerts:
                st.info("暂无告警信息")
                return

            st.subheader("告警摘要")
            for alert in alerts:
                with st.expander(f"{alert['level']} - {alert['title']}"):
                    st.write(alert["description"])
                    st.write(f"时间: {alert['timestamp']}")
                    st.write(f"设备: {alert['device_name']}")

        except Exception as e:
            st.error(f"获取告警信息失败: {str(e)}")
            performance_monitor.record_error()

    async def _render_trend_charts(self):
        """渲染趋势图表"""
        try:
            trends = await self._get_trends()
            if not trends:
                st.info("暂无趋势数据")
                return

            st.subheader("性能趋势")

            # 创建趋势图表
            fig = go.Figure()

            for metric_name, metric_data in trends.items():
                fig.add_trace(
                    go.Scatter(
                        x=metric_data.get("timestamps", []),
                        y=metric_data.get("values", []),
                        name=metric_name,
                    )
                )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"获取趋势数据失败: {str(e)}")
            performance_monitor.record_error()

    def _show_performance_metrics(self):
        """显示性能指标"""
        try:
            metrics = performance_monitor.get_metrics()

            st.subheader("系统性能")

            cols = st.columns(3)

            cols[0].metric(
                "平均响应时间", f"{metrics.get('avg_response_time', 0):.2f}ms"
            )

            cols[1].metric("内存使用", format_bytes(metrics.get("memory_usage", 0)))

            cols[2].metric("CPU使用率", f"{metrics.get('cpu_usage', 0):.1f}%")

        except Exception as e:
            st.error(f"获取性能指标失败: {str(e)}")
            performance_monitor.record_error()

    def _calculate_delta(self, current: float, previous: float) -> Optional[float]:
        """计算变化率"""
        if previous == 0:
            return None
        return (current - previous) / previous * 100

    async def _get_alerts(self) -> List[Dict[str, Any]]:
        """获取告警信息"""
        # TODO: 实现告警获取逻辑
        return []

    async def _get_trends(self) -> Dict[str, Any]:
        """获取趋势数据"""
        # TODO: 实现趋势数据获取逻辑
        return {}


# 创建设备仪表板实例
device_dashboard = DeviceDashboard()

# 渲染页面
if __name__ == "__main__":
    asyncio.run(device_dashboard.render())
