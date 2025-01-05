"""
Monitoring System Manager Module
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from .alerts import AlertManager
from .collector import MetricsCollector
from .dashboard import DashboardGenerator
from .exporter import MetricsExporter, MetricsVisualizer, PrometheusExporter
from .logging import MonitoringLogger
from .middleware import MonitoringMiddleware, RateLimitMiddleware
from .notifications import NotificationManager
from .reporter import ReportGenerator
from .service import MonitoringService
from .settings import MonitoringSettings

logger = logging.getLogger(__name__)


class MonitoringManager:
    """Class for managing the monitoring system"""

    def __init__(self, settings: MonitoringSettings, config_path: Optional[str] = None):
        """Initialize monitoring manager"""
        self.settings = settings
        self.config_path = config_path

        # Initialize components
        self._setup_logging()
        self._setup_components()
        self._setup_tasks()

    def _setup_logging(self):
        """Set up logging"""
        self.logger = MonitoringLogger(
            name="monitoring",
            log_dir=self.settings.get_log_dir(),
            level=getattr(logging, self.settings.logging.level.upper()),
            max_bytes=self.settings.logging.max_size,
            backup_count=self.settings.logging.backup_count,
            include_timestamp=True,
        )

    def _setup_components(self):
        """Set up monitoring components"""
        # Create service
        self.service = MonitoringService(self.settings)

        # Create collectors
        self.collector = MetricsCollector()

        # Create alert manager
        self.alert_manager = AlertManager()
        self._setup_alert_rules()

        # Create notification manager
        self.notification_manager = NotificationManager()
        self._setup_notification_channels()

        # Create dashboard generator
        self.dashboard_generator = DashboardGenerator(
            title="NCOD Monitoring", uid="ncod-monitoring"
        )
        self._setup_dashboards()

        # Create exporters
        self.metrics_exporter = MetricsExporter(
            output_dir=self.settings.get_metrics_dir()
        )
        self.metrics_visualizer = MetricsVisualizer(
            output_dir=os.path.join(self.settings.get_metrics_dir(), "visualizations")
        )
        self.prometheus_exporter = PrometheusExporter(
            output_dir=self.settings.get_prometheus_dir()
        )

        # Create report generator
        self.report_generator = ReportGenerator(
            template_dir=os.path.join(os.path.dirname(__file__), "templates"),
            output_dir=os.path.join(self.settings.get_data_dir(), "reports"),
            static_dir=os.path.join(self.settings.get_data_dir(), "static"),
        )

    def _setup_alert_rules(self):
        """Set up alert rules"""
        # System alerts
        self.alert_manager.create_system_alerts(
            thresholds=self.settings.alerts.thresholds
        )

        # API alerts
        self.alert_manager.create_api_alerts()

        # Node alerts
        self.alert_manager.create_node_alerts()

        # Database alerts
        self.alert_manager.create_database_alerts()

        # Cache alerts
        self.alert_manager.create_cache_alerts()

        # Save alert rules
        self.alert_manager.save_rules(
            os.path.join(self.settings.get_data_dir(), "alerts")
        )

    def _setup_notification_channels(self):
        """Set up notification channels"""
        # Email notifications
        if self.settings.alertmanager.smtp_host:
            from .notifications import EmailChannel

            self.notification_manager.add_channel(
                EmailChannel(
                    name="email",
                    smtp_host=self.settings.alertmanager.smtp_host,
                    smtp_port=self.settings.alertmanager.smtp_port,
                    username=self.settings.alertmanager.smtp_username,
                    password=self.settings.alertmanager.smtp_password,
                    from_address=self.settings.alertmanager.smtp_username,
                    to_addresses=["admin@example.com"],  # TODO: Configure recipients
                )
            )

        # Slack notifications
        if self.settings.alertmanager.slack_api_url:
            from .notifications import SlackChannel

            self.notification_manager.add_channel(
                SlackChannel(
                    name="slack",
                    webhook_url=self.settings.alertmanager.slack_api_url,
                    channel=self.settings.alertmanager.slack_channel,
                )
            )

        # Save notification config
        self.notification_manager.save_config(
            os.path.join(self.settings.get_data_dir(), "notifications")
        )

    def _setup_dashboards(self):
        """Set up monitoring dashboards"""
        # System metrics dashboard
        self.dashboard_generator.add_system_metrics_panel(
            gridPos={"x": 0, "y": 0, "w": 24, "h": 8}
        )

        # API metrics dashboard
        self.dashboard_generator.add_api_metrics_panel(
            gridPos={"x": 0, "y": 8, "w": 24, "h": 8}
        )

        # Task metrics dashboard
        self.dashboard_generator.add_task_metrics_panel(
            gridPos={"x": 0, "y": 16, "w": 24, "h": 8}
        )

        # Node metrics dashboard
        self.dashboard_generator.add_node_metrics_panel(
            gridPos={"x": 0, "y": 24, "w": 24, "h": 8}
        )

        # Database metrics dashboard
        self.dashboard_generator.add_database_metrics_panel(
            gridPos={"x": 0, "y": 32, "w": 24, "h": 8}
        )

        # Cache metrics dashboard
        self.dashboard_generator.add_cache_metrics_panel(
            gridPos={"x": 0, "y": 40, "w": 24, "h": 8}
        )

        # Save dashboard
        self.dashboard_generator.save(
            os.path.join(self.settings.get_data_dir(), "dashboards")
        )

    def _setup_tasks(self):
        """Set up background tasks"""
        self.tasks = []

    async def start(self):
        """Start monitoring system"""
        try:
            # Start monitoring service
            await self.service.start()

            # Start background tasks
            self.tasks = [
                asyncio.create_task(self._collect_metrics()),
                asyncio.create_task(self._check_alerts()),
                asyncio.create_task(self._export_metrics()),
                asyncio.create_task(self._generate_reports()),
            ]

            logger.info("Monitoring system started")

        except Exception as e:
            logger.error(f"Failed to start monitoring system: {e}")
            raise

    async def stop(self):
        """Stop monitoring system"""
        try:
            # Stop monitoring service
            await self.service.stop()

            # Cancel background tasks
            for task in self.tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)
            self.tasks = []

            logger.info("Monitoring system stopped")

        except Exception as e:
            logger.error(f"Failed to stop monitoring system: {e}")
            raise

    async def _collect_metrics(self):
        """Collect metrics periodically"""
        while True:
            try:
                # Get collection interval
                interval = self.settings.get_collection_interval()

                # Collect metrics
                metrics = await self.collector.collect_all()

                # Store metrics
                await self.service.store_metrics(metrics)

                # Export to Prometheus
                if self.settings.prometheus.host:
                    await self.prometheus_exporter.export_metrics(metrics)

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

            await asyncio.sleep(interval.total_seconds())

    async def _check_alerts(self):
        """Check alerts periodically"""
        while True:
            try:
                # Get alert interval
                interval = self.settings.get_alert_interval()

                # Get current metrics
                metrics = await self.service.get_current_metrics()

                # Check alert rules
                alerts = await self.alert_manager.check_rules(metrics)

                # Send notifications
                for alert in alerts:
                    await self.notification_manager.send_notification(
                        subject=alert["summary"],
                        message=alert["description"],
                        channels=self.settings.alerts.notification_channels,
                    )

            except Exception as e:
                logger.error(f"Error checking alerts: {e}")

            await asyncio.sleep(interval.total_seconds())

    async def _export_metrics(self):
        """Export metrics periodically"""
        while True:
            try:
                # Get export interval
                interval = timedelta(seconds=self.settings.metrics.export_interval)

                # Get metrics for export
                metrics = await self.service.get_metrics_for_export()

                # Export metrics
                await self.metrics_exporter.export_metrics(
                    metrics=metrics, format="json"
                )

                # Create visualizations
                await self.metrics_visualizer.create_visualizations(metrics)

            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")

            await asyncio.sleep(interval.total_seconds())

    async def _generate_reports(self):
        """Generate reports periodically"""
        while True:
            try:
                # Generate daily report at midnight
                now = datetime.now()
                next_report = now.replace(hour=0, minute=0, second=0, microsecond=0)
                if next_report <= now:
                    next_report = next_report.replace(day=next_report.day + 1)

                # Wait until next report time
                await asyncio.sleep((next_report - now).total_seconds())

                # Get metrics for report
                metrics = await self.service.get_metrics_for_report()

                # Generate reports
                await self.report_generator.generate_summary_report(
                    metrics=metrics, start_time=now, end_time=next_report
                )

                await self.report_generator.generate_alert_report(
                    alerts=await self.service.get_alerts_for_report(),
                    start_time=now,
                    end_time=next_report,
                )

                await self.report_generator.generate_performance_report(
                    metrics=metrics, start_time=now, end_time=next_report
                )

            except Exception as e:
                logger.error(f"Error generating reports: {e}")

    def get_middleware(self) -> list:
        """Get monitoring middleware"""
        return [
            MonitoringMiddleware(
                system_metrics_interval=self.settings.metrics.collection_interval
            ),
            RateLimitMiddleware(
                rate_limit=self.settings.alerts.thresholds.get("rate_limit", 100),
                window_size=60,
            ),
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.service.get_current_metrics()

    def get_alerts(self) -> list:
        """Get current alerts"""
        return self.service.get_current_alerts()

    def get_status(self) -> Dict[str, Any]:
        """Get monitoring system status"""
        return {
            "status": "running" if self.tasks else "stopped",
            "uptime": self.service.get_uptime(),
            "metrics_count": self.service.get_metrics_count(),
            "alerts_count": self.service.get_alerts_count(),
            "last_collection": self.service.get_last_collection_time(),
            "last_alert_check": self.service.get_last_alert_check_time(),
            "last_export": self.service.get_last_export_time(),
            "last_report": self.service.get_last_report_time(),
        }
