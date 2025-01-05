"""
Monitoring Alerts Module
"""

import os
from datetime import timedelta
from typing import Any, Dict, List, Optional

import yaml


class AlertRule:
    """Class representing a Prometheus alert rule"""

    def __init__(
        self,
        name: str,
        expr: str,
        duration: str,
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None,
    ):
        """Initialize alert rule"""
        self.name = name
        self.expr = expr
        self.duration = duration
        self.labels = labels or {}
        self.annotations = annotations or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        rule_dict = {"alert": self.name, "expr": self.expr, "for": self.duration}

        if self.labels:
            rule_dict["labels"] = self.labels
        if self.annotations:
            rule_dict["annotations"] = self.annotations

        return rule_dict


class AlertRuleGroup:
    """Class representing a group of alert rules"""

    def __init__(self, name: str, rules: Optional[List[AlertRule]] = None):
        """Initialize alert rule group"""
        self.name = name
        self.rules = rules or []

    def add_rule(self, rule: AlertRule):
        """Add a rule to the group"""
        self.rules.append(rule)

    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary"""
        return {"name": self.name, "rules": [rule.to_dict() for rule in self.rules]}


class AlertManager:
    """Class for managing Prometheus alert rules"""

    def __init__(self):
        """Initialize alert manager"""
        self.groups: List[AlertRuleGroup] = []

    def add_group(self, group: AlertRuleGroup):
        """Add a rule group"""
        self.groups.append(group)

    def create_system_alerts(self, thresholds: Dict[str, float]):
        """Create system monitoring alerts"""
        group = AlertRuleGroup("system_alerts")

        # CPU usage alert
        group.add_rule(
            AlertRule(
                name="HighCPUUsage",
                expr=f"100 - system_cpu_percent{{type='idle'}} > \
                     {thresholds['cpu_usage']}",
                duration="5m",
                labels={"severity": "warning", "category": "system"},
                annotations={
                    "summary": "High CPU usage detected",
                    "description": "CPU usage is above {{ $value }}% for 5 minutes",
                },
            )
        )

        # Memory usage alert
        group.add_rule(
            AlertRule(
                name="HighMemoryUsage",
                expr=f"system_memory_bytes{{type='used'}} / \
                     system_memory_bytes{{type='total'}} * 100 > \
                          {thresholds['memory_usage']}",
                duration="5m",
                labels={"severity": "warning", "category": "system"},
                annotations={
                    "summary": "High memory usage detected",
                    "description": "Memory usage is above {{ $value }}% for 5 minutes",
                },
            )
        )

        # Disk usage alert
        group.add_rule(
            AlertRule(
                name="HighDiskUsage",
                expr=f"100 - node_filesystem_avail_bytes{{mountpoint='/'}} / \
                     node_filesystem_size_bytes{{mountpoint='/'}} * 100 > \
                          {thresholds['disk_usage']}",
                duration="5m",
                labels={"severity": "warning", "category": "system"},
                annotations={
                    "summary": "High disk usage detected",
                    "description": "Disk usage is above {{ $value }}% for 5 minutes",
                },
            )
        )

        self.add_group(group)

    def create_api_alerts(self):
        """Create API monitoring alerts"""
        group = AlertRuleGroup("api_alerts")

        # High error rate alert
        group.add_rule(
            AlertRule(
                name="HighErrorRate",
                expr="sum(rate(api_request_duration_seconds_count{status=~'5..'}[5m])) \
                     / sum(rate(api_request_duration_seconds_count[5m])) * 100 > 5",
                duration="5m",
                labels={"severity": "critical", "category": "api"},
                annotations={
                    "summary": "High API error rate detected",
                    "description": "API error rate is above 5% for 5 minutes",
                },
            )
        )

        # Slow response time alert
        group.add_rule(
            AlertRule(
                name="SlowResponseTime",
                expr="rate(api_request_duration_seconds_sum[5m]) / \
                     rate(api_request_duration_seconds_count[5m]) > 1",
                duration="5m",
                labels={"severity": "warning", "category": "api"},
                annotations={
                    "summary": "Slow API response time detected",
                    "description": "Average response time is above 1 second for 5 \
                         minutes",
                },
            )
        )

        self.add_group(group)

    def create_node_alerts(self):
        """Create node monitoring alerts"""
        group = AlertRuleGroup("node_alerts")

        # Node down alert
        group.add_rule(
            AlertRule(
                name="NodeDown",
                expr="node_status == 0",
                duration="5m",
                labels={"severity": "critical", "category": "node"},
                annotations={
                    "summary": "Node is down",
                    "description": "Node {{ $labels.node_id }} ({{ $labels.role }}) is \
                         down for 5 minutes",
                },
            )
        )

        # High node latency alert
        group.add_rule(
            AlertRule(
                name="HighNodeLatency",
                expr="rate(node_latency_seconds_sum[5m]) / \
                     rate(node_latency_seconds_count[5m]) > 0.1",
                duration="5m",
                labels={"severity": "warning", "category": "node"},
                annotations={
                    "summary": "High node latency detected",
                    "description": "Node {{ $labels.node_id }} has high latency \
                         (>100ms) for operation {{ $labels.operation }}",
                },
            )
        )

        self.add_group(group)

    def create_database_alerts(self):
        """Create database monitoring alerts"""
        group = AlertRuleGroup("database_alerts")

        # Connection pool exhaustion alert
        group.add_rule(
            AlertRule(
                name="ConnectionPoolExhaustion",
                expr="db_connection_pool_size{status='idle'} < 2",
                duration="5m",
                labels={"severity": "warning", "category": "database"},
                annotations={
                    "summary": "Database connection pool near exhaustion",
                    "description": "Less than 2 idle connections available in the pool",
                },
            )
        )

        # Slow query alert
        group.add_rule(
            AlertRule(
                name="SlowQueries",
                expr="rate(db_query_duration_seconds_sum[5m]) / \
                     rate(db_query_duration_seconds_count[5m]) > 1",
                duration="5m",
                labels={"severity": "warning", "category": "database"},
                annotations={
                    "summary": "Slow database queries detected",
                    "description": "Average query duration is above 1 second for \
                         operation {{ $labels.operation }}",
                },
            )
        )

        self.add_group(group)

    def create_cache_alerts(self):
        """Create cache monitoring alerts"""
        group = AlertRuleGroup("cache_alerts")

        # Low cache hit rate alert
        group.add_rule(
            AlertRule(
                name="LowCacheHitRate",
                expr="sum(rate(cache_hit_count_total[5m])) / \
                     (sum(rate(cache_hit_count_total[5m])) \
                sum(rate(cache_miss_count_total[5m]))) * 100 < 50",
                duration="5m",
                labels={"severity": "warning", "category": "cache"},
                annotations={
                    "summary": "Low cache hit rate detected",
                    "description": "Cache hit rate is below 50% for cache {{ \
                         $labels.cache }}",
                },
            )
        )

        # High cache memory usage alert
        group.add_rule(
            AlertRule(
                name="HighCacheMemoryUsage",
                expr="cache_size_bytes / 1024 / 1024 > 1000",
                duration="5m",
                labels={"severity": "warning", "category": "cache"},
                annotations={
                    "summary": "High cache memory usage",
                    "description": "Cache {{ $labels.cache }} is using more than 1GB of \
                         \
                         \
                         \
                         \
                         \
                         \
                         \
                         \
                         \
                         \
                         \
                         \
                         \
                         memory",
                },
            )
        )

        self.add_group(group)

    def save_rules(self, output_dir: str):
        """Save alert rules to file"""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "alert_rules.yml")

        rules_dict = {"groups": [group.to_dict() for group in self.groups]}

        with open(output_path, "w") as f:
            yaml.dump(rules_dict, f, default_flow_style=False)

        return output_path

    def get_yaml(self) -> str:
        """Get rules as YAML string"""
        rules_dict = {"groups": [group.to_dict() for group in self.groups]}
        return yaml.dump(rules_dict, default_flow_style=False)

    def get_dict(self) -> Dict[str, Any]:
        """Get rules as dictionary"""
        return {"groups": [group.to_dict() for group in self.groups]}
