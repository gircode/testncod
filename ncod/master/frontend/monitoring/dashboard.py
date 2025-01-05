"""
Grafana Dashboard Generator Module
"""

import json
import os
from typing import Any, Dict, List, Optional


class DashboardGenerator:
    """Helper class for generating Grafana dashboards"""

    def __init__(self, title: str, uid: Optional[str] = None):
        """Initialize dashboard generator"""
        self.dashboard = {
            "title": title,
            "uid": uid or title.lower().replace(" ", "-"),
            "tags": ["ncod", "generated"],
            "timezone": "browser",
            "schemaVersion": 21,
            "version": 0,
            "refresh": "10s",
            "panels": [],
            "templating": {"list": []},
            "time": {"from": "now-6h", "to": "now"},
        }
        self.panel_id = 0

    def add_system_metrics_panel(self, gridPos: Dict[str, int]):
        """Add system metrics panel"""
        self.panel_id += 1
        panel = {
            "id": self.panel_id,
            "title": "System Metrics",
            "type": "row",
            "gridPos": gridPos,
            "collapsed": False,
            "panels": [
                self._create_cpu_usage_panel(),
                self._create_memory_usage_panel(),
                self._create_disk_usage_panel(),
            ],
        }
        self.dashboard["panels"].append(panel)

    def add_api_metrics_panel(self, gridPos: Dict[str, int]):
        """Add API metrics panel"""
        self.panel_id += 1
        panel = {
            "id": self.panel_id,
            "title": "API Metrics",
            "type": "row",
            "gridPos": gridPos,
            "collapsed": False,
            "panels": [
                self._create_request_duration_panel(),
                self._create_request_size_panel(),
                self._create_error_rate_panel(),
            ],
        }
        self.dashboard["panels"].append(panel)

    def add_task_metrics_panel(self, gridPos: Dict[str, int]):
        """Add task metrics panel"""
        self.panel_id += 1
        panel = {
            "id": self.panel_id,
            "title": "Task Metrics",
            "type": "row",
            "gridPos": gridPos,
            "collapsed": False,
            "panels": [
                self._create_task_count_panel(),
                self._create_task_duration_panel(),
                self._create_queue_size_panel(),
            ],
        }
        self.dashboard["panels"].append(panel)

    def add_node_metrics_panel(self, gridPos: Dict[str, int]):
        """Add node metrics panel"""
        self.panel_id += 1
        panel = {
            "id": self.panel_id,
            "title": "Node Metrics",
            "type": "row",
            "gridPos": gridPos,
            "collapsed": False,
            "panels": [
                self._create_node_status_panel(),
                self._create_node_latency_panel(),
            ],
        }
        self.dashboard["panels"].append(panel)

    def add_database_metrics_panel(self, gridPos: Dict[str, int]):
        """Add database metrics panel"""
        self.panel_id += 1
        panel = {
            "id": self.panel_id,
            "title": "Database Metrics",
            "type": "row",
            "gridPos": gridPos,
            "collapsed": False,
            "panels": [
                self._create_db_connections_panel(),
                self._create_query_duration_panel(),
                self._create_transaction_count_panel(),
            ],
        }
        self.dashboard["panels"].append(panel)

    def add_cache_metrics_panel(self, gridPos: Dict[str, int]):
        """Add cache metrics panel"""
        self.panel_id += 1
        panel = {
            "id": self.panel_id,
            "title": "Cache Metrics",
            "type": "row",
            "gridPos": gridPos,
            "collapsed": False,
            "panels": [
                self._create_cache_hit_rate_panel(),
                self._create_cache_size_panel(),
            ],
        }
        self.dashboard["panels"].append(panel)

    def _create_cpu_usage_panel(self) -> Dict[str, Any]:
        """Create CPU usage panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "CPU Usage",
            "type": "gauge",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "100 - system_cpu_percent{type='idle'}",
                    "legendFormat": "CPU Usage",
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"value": 0, "color": "green"},
                            {"value": 70, "color": "yellow"},
                            {"value": 85, "color": "red"},
                        ],
                    },
                    "unit": "percent",
                }
            },
        }

    def _create_memory_usage_panel(self) -> Dict[str, Any]:
        """Create memory usage panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Memory Usage",
            "type": "gauge",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "system_memory_bytes{type='used'} / \
                         system_memory_bytes{type='total'} * 100",
                    "legendFormat": "Memory Usage",
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"value": 0, "color": "green"},
                            {"value": 70, "color": "yellow"},
                            {"value": 85, "color": "red"},
                        ],
                    },
                    "unit": "percent",
                }
            },
        }

    def _create_disk_usage_panel(self) -> Dict[str, Any]:
        """Create disk usage panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Disk Usage",
            "type": "gauge",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "100 - node_filesystem_avail_bytes{mountpoint='/'} / \
                         node_filesystem_size_bytes{mountpoint='/'} * 100",
                    "legendFormat": "Disk Usage",
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"value": 0, "color": "green"},
                            {"value": 70, "color": "yellow"},
                            {"value": 85, "color": "red"},
                        ],
                    },
                    "unit": "percent",
                }
            },
        }

    def _create_request_duration_panel(self) -> Dict[str, Any]:
        """Create request duration panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Request Duration",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "rate(api_request_duration_seconds_sum[5m]) / \
                         rate(api_request_duration_seconds_count[5m])",
                    "legendFormat": "{{method}} {{endpoint}}",
                }
            ],
            "yaxes": [{"format": "s"}, {"format": "short"}],
        }

    def _create_request_size_panel(self) -> Dict[str, Any]:
        """Create request size panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Request Size",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "rate(api_request_size_bytes_sum[5m])",
                    "legendFormat": "{{method}} {{endpoint}}",
                }
            ],
            "yaxes": [{"format": "bytes"}, {"format": "short"}],
        }

    def _create_error_rate_panel(self) -> Dict[str, Any]:
        """Create error rate panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Error Rate",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "sum(rate(api_request_duration_seconds_count{status=~'5..'}[5m])) / sum(rate(api_request_duration_seconds_count[5m])) * 100",
                    "legendFormat": "Error Rate",
                }
            ],
            "yaxes": [{"format": "percent"}, {"format": "short"}],
        }

    def _create_task_count_panel(self) -> Dict[str, Any]:
        """Create task count panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Task Count",
            "type": "stat",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "sum(task_count_total) by (status)",
                    "legendFormat": "{{status}}",
                }
            ],
        }

    def _create_task_duration_panel(self) -> Dict[str, Any]:
        """Create task duration panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Task Duration",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "rate(task_duration_seconds_sum[5m]) / \
                         rate(task_duration_seconds_count[5m])",
                    "legendFormat": "{{type}}",
                }
            ],
            "yaxes": [{"format": "s"}, {"format": "short"}],
        }

    def _create_queue_size_panel(self) -> Dict[str, Any]:
        """Create queue size panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Queue Size",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [{"expr": "task_queue_size", "legendFormat": "{{queue}}"}],
        }

    def _create_node_status_panel(self) -> Dict[str, Any]:
        """Create node status panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Node Status",
            "type": "stat",
            "datasource": "Prometheus",
            "targets": [
                {"expr": "node_status", "legendFormat": "{{node_id}} ({{role}})"}
            ],
            "fieldConfig": {
                "defaults": {
                    "mappings": [
                        {"value": "0", "text": "Down"},
                        {"value": "1", "text": "Up"},
                    ],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"value": 0, "color": "red"},
                            {"value": 1, "color": "green"},
                        ],
                    },
                }
            },
        }

    def _create_node_latency_panel(self) -> Dict[str, Any]:
        """Create node latency panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Node Latency",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "rate(node_latency_seconds_sum[5m]) / \
                         rate(node_latency_seconds_count[5m])",
                    "legendFormat": "{{node_id}} - {{operation}}",
                }
            ],
            "yaxes": [{"format": "s"}, {"format": "short"}],
        }

    def _create_db_connections_panel(self) -> Dict[str, Any]:
        """Create database connections panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Database Connections",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {"expr": "db_connection_pool_size", "legendFormat": "{{status}}"}
            ],
        }

    def _create_query_duration_panel(self) -> Dict[str, Any]:
        """Create query duration panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Query Duration",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "rate(db_query_duration_seconds_sum[5m]) / \
                         rate(db_query_duration_seconds_count[5m])",
                    "legendFormat": "{{operation}}",
                }
            ],
            "yaxes": [{"format": "s"}, {"format": "short"}],
        }

    def _create_transaction_count_panel(self) -> Dict[str, Any]:
        """Create transaction count panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Transaction Count",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "rate(db_transaction_count_total[5m])",
                    "legendFormat": "{{status}}",
                }
            ],
        }

    def _create_cache_hit_rate_panel(self) -> Dict[str, Any]:
        """Create cache hit rate panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Cache Hit Rate",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [
                {
                    "expr": "sum(rate(cache_hit_count_total[5m])) / \
                         (sum(rate(cache_hit_count_total[5m])) \
                    sum(rate(cache_miss_count_total[5m]))) * 100",
                    "legendFormat": "{{cache}}",
                }
            ],
            "yaxes": [{"format": "percent"}, {"format": "short"}],
        }

    def _create_cache_size_panel(self) -> Dict[str, Any]:
        """Create cache size panel"""
        self.panel_id += 1
        return {
            "id": self.panel_id,
            "title": "Cache Size",
            "type": "graph",
            "datasource": "Prometheus",
            "targets": [{"expr": "cache_size_bytes", "legendFormat": "{{cache}}"}],
            "yaxes": [{"format": "bytes"}, {"format": "short"}],
        }

    def save(self, output_dir: str):
        """Save dashboard to file"""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{self.dashboard['uid']}.json")

        with open(output_path, "w") as f:
            json.dump(self.dashboard, f, indent=2)

        return output_path

    def get_json(self) -> str:
        """Get dashboard as JSON string"""
        return json.dumps(self.dashboard, indent=2)

    def get_dict(self) -> Dict[str, Any]:
        """Get dashboard as dictionary"""
        return self.dashboard
