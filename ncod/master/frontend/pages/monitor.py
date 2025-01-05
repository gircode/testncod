"""Monitor模块"""

import datetime
import json
import logging
from typing import Dict, List, Optional

from database import db_manager
from models.user import AlertRule, Device, DeviceMetric, SystemAlert
from pywebio.input import input, input_group, select, textarea
from pywebio.output import clear, put_error, put_html, put_loading, toast
from pywebio.session import info as session_info
from pywebio.session import run_js, set_env

logger = logging.getLogger(__name__)


def get_system_metrics(hours: int = 24) -> Dict[str, List[Dict]]:
    """获取系统性能指标"""
    try:
        with db_manager.get_session() as session:
            time_threshold = datetime.datetime.utcnow() - datetime.timedelta(
                hours=hours
            )
            metrics = (
                session.query(DeviceMetric)
                .filter(DeviceMetric.collected_at >= time_threshold)
                .order_by(DeviceMetric.collected_at.asc())
                .all()
            )

            # 按指标类型分组
            grouped_metrics = {}
            for metric in metrics:
                if metric.metric_type not in grouped_metrics:
                    grouped_metrics[metric.metric_type] = []
                grouped_metrics[metric.metric_type].append(
                    {
                        "device_id": metric.device_id,
                        "device_name": (
                            metric.device.name if metric.device else "Unknown"
                        ),
                        "value": metric.value,
                        "time": metric.collected_at.isoformat(),
                    }
                )

            return grouped_metrics
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {}


def get_alert_rules() -> List[Dict]:
    """获取告警规则"""
    try:
        with db_manager.get_session() as session:
            rules = session.query(AlertRule).all()
            return [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "metric_type": rule.metric_type,
                    "condition": rule.condition,
                    "threshold": rule.threshold,
                    "severity": rule.severity,
                    "enabled": rule.enabled,
                    "created_at": rule.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for rule in rules
            ]
    except Exception as e:
        logger.error(f"Failed to get alert rules: {e}")
        return []


def get_recent_alerts(limit: int = 50) -> List[Dict]:
    """获取最近告警"""
    try:
        with db_manager.get_session() as session:
            alerts = (
                session.query(SystemAlert)
                .order_by(SystemAlert.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "status": alert.status,
                    "device": (
                        {
                            "id": alert.device.id,
                            "name": alert.device.name,
                            "device_id": alert.device.device_id,
                        }
                        if alert.device
                        else None
                    ),
                    "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "resolved_at": (
                        alert.resolved_at.strftime("%Y-%m-%d %H:%M:%S")
                        if alert.resolved_at
                        else None
                    ),
                }
                for alert in alerts
            ]
    except Exception as e:
        logger.error(f"Failed to get recent alerts: {e}")
        return []


async def create_alert_rule(rule_data: Dict) -> bool:
    """创建告警规则"""
    try:
        with db_manager.get_session() as session:
            rule = AlertRule(
                name=rule_data["name"],
                metric_type=rule_data["metric_type"],
                condition=rule_data["condition"],
                threshold=rule_data["threshold"],
                severity=rule_data["severity"],
                enabled=True,
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            session.add(rule)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        return False


async def update_alert_rule(rule_id: int, rule_data: Dict) -> bool:
    """更新告警规则"""
    try:
        with db_manager.get_session() as session:
            rule = session.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not rule:
                return False

            rule.name = rule_data.get("name", rule.name)
            rule.metric_type = rule_data.get("metric_type", rule.metric_type)
            rule.condition = rule_data.get("condition", rule.condition)
            rule.threshold = rule_data.get("threshold", rule.threshold)
            rule.severity = rule_data.get("severity", rule.severity)
            rule.enabled = rule_data.get("enabled", rule.enabled)
            rule.updated_at = datetime.datetime.utcnow()

            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to update alert rule: {e}")
        return False


async def resolve_alert(alert_id: int) -> bool:
    """解决告警"""
    try:
        with db_manager.get_session() as session:
            alert = (
                session.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
            )
            if not alert or alert.status == "resolved":
                return False

            alert.status = "resolved"
            alert.resolved_at = datetime.datetime.utcnow()
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        return False


async def monitor_page():
    """监控和告警页面"""
    set_env(title="系统监控")

    # 页面样式
    style = """
    <style>
        .monitor-page {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .monitor-header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .monitor-title {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
        }
        .monitor-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .monitor-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card-title {
            font-size: 18px;
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .metric-chart {
            width: 100%;
            height: 300px;
            margin-top: 20px;
        }
        .alert-list {
            margin-top: 10px;
        }
        .alert-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }
        .alert-item:last-child {
            border-bottom: none;
        }
        .alert-info {
            flex: 1;
        }
        .alert-title {
            font-weight: 500;
            color: #2c3e50;
        }
        .alert-meta {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .severity-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
        }
        .severity-critical {
            background: #fee2e2;
            color: #dc2626;
        }
        .severity-high {
            background: #fef3c7;
            color: #d97706;
        }
        .severity-medium {
            background: #dbeafe;
            color: #2563eb;
        }
        .severity-low {
            background: #dcfce7;
            color: #16a34a;
        }
        .action-button {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        .create-button {
            background: #3b82f6;
            color: white;
        }
        .create-button:hover {
            background: #2563eb;
        }
        .resolve-button {
            background: #10b981;
            color: white;
            padding: 4px 8px;
        }
        .resolve-button:hover {
            background: #059669;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal-content {
            position: relative;
            background: white;
            margin: 100px auto;
            padding: 20px;
            width: 90%;
            max-width: 500px;
            border-radius: 10px;
        }
        .modal-header {
            margin-bottom: 20px;
        }
        .modal-title {
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
        }
        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 24px;
            cursor: pointer;
            color: #64748b;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-label {
            display: block;
            font-size: 14px;
            color: #64748b;
            margin-bottom: 5px;
        }
        .form-input {
            width: 100%;
            padding: 8px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.1);
        }
        .form-select {
            width: 100%;
            padding: 8px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            font-size: 14px;
            background-color: white;
        }
        .modal-footer {
            margin-top: 20px;
            text-align: right;
        }
        .cancel-button {
            background: #e5e7eb;
            color: #374151;
            margin-right: 10px;
        }
        .cancel-button:hover {
            background: #d1d5db;
        }
        .rule-list {
            margin-top: 10px;
        }
        .rule-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }
        .rule-item:last-child {
            border-bottom: none;
        }
        .rule-info {
            flex: 1;
        }
        .rule-name {
            font-weight: 500;
            color: #2c3e50;
        }
        .rule-meta {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-enabled {
            background: #dcfce7;
            color: #16a34a;
        }
        .status-disabled {
            background: #f3f4f6;
            color: #6b7280;
        }
    </style>
    """

    # 获取数据
    metrics = get_system_metrics()
    alerts = get_recent_alerts()
    rules = get_alert_rules()

    # 渲染页面
    clear()
    put_html(style)

    put_html(
        f"""
    <div class="monitor-page">
        <div class="monitor-header">
            <div class="monitor-title">系统监控</div>
            <button class="action-button create-button" \
                 onclick="showCreateRuleModal()">创建告警规则</button>
        </div>
        
        <div class="monitor-grid">
            <!-- 性能指标图表 -->
            <div class="monitor-card">
                <div class="card-title">CPU使用率</div>
                <div id="cpu-chart" class="metric-chart"></div>
            </div>
            <div class="monitor-card">
                <div class="card-title">内存使用率</div>
                <div id="memory-chart" class="metric-chart"></div>
            </div>
            <div class="monitor-card">
                <div class="card-title">磁盘使用率</div>
                <div id="disk-chart" class="metric-chart"></div>
            </div>
            <div class="monitor-card">
                <div class="card-title">网络流量</div>
                <div id="network-chart" class="metric-chart"></div>
            </div>
        </div>
        
        <div class="monitor-grid">
            <!-- 告警列表 -->
            <div class="monitor-card">
                <div class="card-title">最近告警</div>
                <div class="alert-list">
    """
    )

    for alert in alerts:
        severity_class = {
            "critical": "severity-critical",
            "high": "severity-high",
            "medium": "severity-medium",
            "low": "severity-low",
        }.get(alert["severity"], "")

        put_html(
            f"""
            <div class="alert-item">
                <div class="alert-info">
                    <div class="alert-title">{alert['title']}</div>
                    <div class="alert-meta">
                        {alert['message']} | 
                        设备: {alert['device']['name'] if alert['device'] else 'N/A'} | 
                        {alert['created_at']}
                    </div>
                </div>
                <div>
                    <span class="severity-badge \
                         {severity_class}">{alert['severity']}</span>
                    {f'<button class="action-button resolve-button" \
                         onclick="resolveAlert({alert["id"]})">解决</button>' if \
                              alert['status'] != 'resolved' else ''}
                </div>
            </div>
        """
        )

    put_html(
        """
                </div>
            </div>
            
            <!-- 告警规则 -->
            <div class="monitor-card">
                <div class="card-title">告警规则</div>
                <div class="rule-list">
    """
    )

    for rule in rules:
        severity_class = {
            "critical": "severity-critical",
            "high": "severity-high",
            "medium": "severity-medium",
            "low": "severity-low",
        }.get(rule["severity"], "")

        status_class = "status-enabled" if rule["enabled"] else "status-disabled"

        put_html(
            f"""
            <div class="rule-item">
                <div class="rule-info">
                    <div class="rule-name">{rule['name']}</div>
                    <div class="rule-meta">
                        {rule['metric_type']} {rule['condition']} {rule['threshold']} | 
                        创建时间: {rule['created_at']}
                    </div>
                </div>
                <div>
                    <span class="severity-badge \
                         {severity_class}">{rule['severity']}</span>
                    <span class="status-badge {status_class}">{rule['enabled']}</span>
                </div>
            </div>
        """
        )

    put_html(
        """
                </div>
            </div>
        </div>
        
        <!-- 创建告警规则模态框 -->
        <div id="createRuleModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title">创建告警规则</div>
                    <span class="close" onclick="hideCreateRuleModal()">&times;</span>
                </div>
                <div class="form-group">
                    <label class="form-label">规则名称</label>
                    <input type="text" class="form-input" id="rule_name">
                </div>
                <div class="form-group">
                    <label class="form-label">指标类型</label>
                    <select class="form-select" id="metric_type">
                        <option value="cpu">CPU使用率</option>
                        <option value="memory">内存使用率</option>
                        <option value="disk">磁盘使用率</option>
                        <option value="network">网络流量</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">条件</label>
                    <select class="form-select" id="condition">
                        <option value=">">&gt;</option>
                        <option value=">=">&gt;=</option>
                        <option value="<">&lt;</option>
                        <option value="<=">&lt;=</option>
                        <option value="==">==</option>
                        <option value="!=">!=</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">阈值</label>
                    <input type="number" class="form-input" id="threshold">
                </div>
                <div class="form-group">
                    <label class="form-label">严重程度</label>
                    <select class="form-select" id="severity">
                        <option value="critical">严重</option>
                        <option value="high">高</option>
                        <option value="medium">中</option>
                        <option value="low">低</option>
                    </select>
                </div>
                <div class="modal-footer">
                    <button class="action-button cancel-button" \
                         onclick="hideCreateRuleModal()">取消</button>
                    <button class="action-button create-button" \
                         onclick="createRule()">创建</button>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        // 性能指标图表
        const metrics = {json.dumps(metrics)};
        
        // CPU使用率图表
        if (metrics.cpu) {
            const cpuData = metrics.cpu;
            const devices = [...new Set(cpuData.map(m => m.device_name))];
            
            const traces = devices.map(device => {{
                const data = cpuData.filter(m => m.device_name === device);
                return {{
                    x: data.map(d => d.time),
                    y: data.map(d => d.value.value),
                    type: 'scatter',
                    name: device
                }};
            }});
            
            Plotly.newPlot('cpu-chart', traces, {{
                title: 'CPU使用率',
                xaxis: {{ title: '时间' }},
                yaxis: {{ title: '使用率 (%)' }}
            }});
        }}
        
        // 内存使用率图表
        if (metrics.memory) {
            const memoryData = metrics.memory;
            const devices = [...new Set(memoryData.map(m => m.device_name))];
            
            const traces = devices.map(device => {{
                const data = memoryData.filter(m => m.device_name === device);
                return {{
                    x: data.map(d => d.time),
                    y: data.map(d => d.value.value),
                    type: 'scatter',
                    name: device
                }};
            }});
            
            Plotly.newPlot('memory-chart', traces, {{
                title: '内存使用率',
                xaxis: {{ title: '时间' }},
                yaxis: {{ title: '使用率 (%)' }}
            }});
        }}
        
        // 磁盘使用率图表
        if (metrics.disk) {
            const diskData = metrics.disk;
            const devices = [...new Set(diskData.map(m => m.device_name))];
            
            const traces = devices.map(device => {{
                const data = diskData.filter(m => m.device_name === device);
                return {{
                    x: data.map(d => d.time),
                    y: data.map(d => d.value.value),
                    type: 'scatter',
                    name: device
                }};
            }});
            
            Plotly.newPlot('disk-chart', traces, {{
                title: '磁盘使用率',
                xaxis: {{ title: '时间' }},
                yaxis: {{ title: '使用率 (%)' }}
            }});
        }}
        
        // 网络流量图表
        if (metrics.network) {
            const networkData = metrics.network;
            const devices = [...new Set(networkData.map(m => m.device_name))];
            
            const traces = devices.map(device => {{
                const data = networkData.filter(m => m.device_name === device);
                return {{
                    x: data.map(d => d.time),
                    y: data.map(d => d.value.value),
                    type: 'scatter',
                    name: device
                }};
            }});
            
            Plotly.newPlot('network-chart', traces, {{
                title: '网络流量',
                xaxis: {{ title: '时间' }},
                yaxis: {{ title: '流量 (MB/s)' }}
            }});
        }}
        
        // 显示创建规则模态框
        function showCreateRuleModal() {{
            document.getElementById('createRuleModal').style.display = 'block';
        }}
        
        // 隐藏创建规则模态框
        function hideCreateRuleModal() {{
            document.getElementById('createRuleModal').style.display = 'none';
        }}
        
        // 创建告警规则
        function createRule() {{
            const ruleData = {{
                name: document.getElementById('rule_name').value,
                metric_type: document.getElementById('metric_type').value,
                condition: document.getElementById('condition').value,
                threshold: parseFloat(document.getElementById('threshold').value),
                severity: document.getElementById('severity').value
            }};
            
            pywebio.call_js_function('create_alert_rule', ruleData).then(success => {{
                if (success) {{
                    hideCreateRuleModal();
                    location.reload();
                }} else {{
                    alert('创建告警规则失败');
                }}
            }});
        }}
        
        // 解决告警
        function resolveAlert(alertId) {{
            if (confirm('确定要将此告警标记为已解决吗？')) {{
                pywebio.call_js_function('resolve_alert', alertId).then(success => {{
                    if (success) {{
                        location.reload();
                    }} else {{
                        alert('解决告警失败');
                    }}
                }});
            }}
        }}
        
        // WebSocket连接
        const ws = new WebSocket(`ws://${{window.location.host}}/ws/monitor`);
        ws.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            if (data.type === 'metric_update') {{
                // 更新性能图表
                const trace = {{
                    x: [data.time],
                    y: [data.value.value]
                }};
                Plotly.extendTraces(`${{data.metric_type}}-chart`, trace, [0]);
            }} else if (data.type === 'alert') {{
                // 刷新页面以显示新告警
                location.reload();
            }}
        }};
    </script>
    """
    )


if __name__ == "__main__":
    monitor_page()
