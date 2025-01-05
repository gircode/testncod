"""
Monitoring Report Generator Module
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import markdown
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import weasyprint
from jinja2 import Environment, FileSystemLoader


class ReportGenerator:
    """Class for generating monitoring reports"""

    def __init__(
        self, template_dir: str, output_dir: str, static_dir: Optional[str] = None
    ):
        """Initialize report generator"""
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.static_dir = static_dir or os.path.join(template_dir, "static")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Set up Jinja environment
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    def generate_report(
        self,
        data: Dict[str, Any],
        template_name: str,
        output_format: str = "html",
        filename: Optional[str] = None,
    ) -> str:
        """Generate monitoring report"""
        # Load template
        template = self.env.get_template(template_name)

        # Add timestamp to data
        data["generated_at"] = datetime.now().isoformat()

        # Render template
        html_content = template.render(**data)

        # Generate output filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.{output_format}"

        output_path = os.path.join(self.output_dir, filename)

        if output_format == "html":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        elif output_format == "pdf":
            weasyprint.HTML(string=html_content).write_pdf(output_path)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        return output_path

    def generate_summary_report(
        self,
        metrics: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        filename: Optional[str] = None,
    ) -> str:
        """Generate summary report"""
        # Prepare report data
        report_data = {
            "title": "Monitoring Summary Report",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": str(end_time - start_time),
            "metrics": self._process_metrics_for_summary(metrics),
        }

        return self.generate_report(
            data=report_data, template_name="summary_report.html", filename=filename
        )

    def generate_alert_report(
        self,
        alerts: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime,
        filename: Optional[str] = None,
    ) -> str:
        """Generate alert report"""
        # Prepare report data
        report_data = {
            "title": "Alert History Report",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": str(end_time - start_time),
            "alerts": self._process_alerts_for_report(alerts),
        }

        return self.generate_report(
            data=report_data, template_name="alert_report.html", filename=filename
        )

    def generate_performance_report(
        self,
        metrics: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        filename: Optional[str] = None,
    ) -> str:
        """Generate performance report"""
        # Prepare report data
        report_data = {
            "title": "Performance Analysis Report",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": str(end_time - start_time),
            "metrics": self._process_metrics_for_performance(metrics),
        }

        return self.generate_report(
            data=report_data, template_name="performance_report.html", filename=filename
        )

    def _process_metrics_for_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process metrics for summary report"""
        summary = {
            "system": self._process_system_metrics(metrics.get("system", {})),
            "api": self._process_api_metrics(metrics.get("api", {})),
            "database": self._process_database_metrics(metrics.get("database", {})),
            "cache": self._process_cache_metrics(metrics.get("cache", {})),
        }

        return summary

    def _process_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process system metrics"""
        return {
            "cpu_usage": {
                "average": self._calculate_average(metrics.get("cpu_usage", [])),
                "peak": self._calculate_peak(metrics.get("cpu_usage", [])),
                "chart": self._create_time_series_chart(
                    metrics.get("cpu_usage", []), "CPU Usage"
                ),
            },
            "memory_usage": {
                "average": self._calculate_average(metrics.get("memory_usage", [])),
                "peak": self._calculate_peak(metrics.get("memory_usage", [])),
                "chart": self._create_time_series_chart(
                    metrics.get("memory_usage", []), "Memory Usage"
                ),
            },
        }

    def _process_api_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process API metrics"""
        return {
            "request_count": len(metrics.get("requests", [])),
            "error_rate": self._calculate_error_rate(metrics.get("requests", [])),
            "response_times": {
                "average": self._calculate_average(metrics.get("response_times", [])),
                "p95": self._calculate_percentile(
                    metrics.get("response_times", []), 95
                ),
                "p99": self._calculate_percentile(
                    metrics.get("response_times", []), 99
                ),
                "chart": self._create_time_series_chart(
                    metrics.get("response_times", []), "Response Times"
                ),
            },
        }

    def _process_database_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process database metrics"""
        return {
            "query_times": {
                "average": self._calculate_average(metrics.get("query_times", [])),
                "p95": self._calculate_percentile(metrics.get("query_times", []), 95),
                "chart": self._create_time_series_chart(
                    metrics.get("query_times", []), "Query Times"
                ),
            },
            "connection_pool": {
                "utilization": self._calculate_average(
                    metrics.get("connection_pool_utilization", [])
                ),
                "chart": self._create_time_series_chart(
                    metrics.get("connection_pool_utilization", []),
                    "Connection Pool Utilization",
                ),
            },
        }

    def _process_cache_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process cache metrics"""
        return {
            "hit_rate": {
                "average": self._calculate_average(metrics.get("hit_rate", [])),
                "chart": self._create_time_series_chart(
                    metrics.get("hit_rate", []), "Cache Hit Rate"
                ),
            },
            "memory_usage": {
                "average": self._calculate_average(metrics.get("memory_usage", [])),
                "peak": self._calculate_peak(metrics.get("memory_usage", [])),
                "chart": self._create_time_series_chart(
                    metrics.get("memory_usage", []), "Cache Memory Usage"
                ),
            },
        }

    def _process_alerts_for_report(
        self, alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process alerts for report"""
        # Group alerts by severity
        severity_groups = {}
        for alert in alerts:
            severity = alert.get("severity", "unknown")
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(alert)

        # Process each severity group
        processed_alerts = {}
        for severity, alerts in severity_groups.items():
            processed_alerts[severity] = {
                "count": len(alerts),
                "alerts": sorted(
                    alerts, key=lambda x: x.get("timestamp", ""), reverse=True
                ),
            }

        return processed_alerts

    def _calculate_average(self, values: List[float]) -> float:
        """Calculate average of values"""
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _calculate_peak(self, values: List[float]) -> float:
        """Calculate peak value"""
        if not values:
            return 0.0
        return max(values)

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        return pd.Series(values).quantile(percentile / 100)

    def _calculate_error_rate(self, requests: List[Dict[str, Any]]) -> float:
        """Calculate error rate"""
        if not requests:
            return 0.0

        error_count = sum(1 for req in requests if req.get("status_code", 200) >= 500)
        return (error_count / len(requests)) * 100

    def _create_time_series_chart(
        self, data: List[Dict[str, Union[str, float]]], title: str
    ) -> str:
        """Create time series chart"""
        if not data:
            return ""

        # Create DataFrame
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Create plot
        plt.figure(figsize=(10, 4))
        plt.plot(df.index, df["value"])
        plt.title(title)
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot to static directory
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)

        filename = f"{title.lower().replace(' ', \
             '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = os.path.join(self.static_dir, filename)
        plt.savefig(output_path)
        plt.close()

        return f"static/{filename}"
