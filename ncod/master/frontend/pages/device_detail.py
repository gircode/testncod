"""Device Detail模块"""

import datetime
import json
import logging
from typing import Dict, List, Optional

from database import db_manager
from models.user import Device, DeviceMetric, Task, User
from pywebio.input import input, input_group, select, textarea
from pywebio.output import clear, put_error, put_html, put_loading, toast
from pywebio.session import info as session_info
from pywebio.session import run_js, set_env

logger = logging.getLogger(__name__)


def get_device_metrics(device_id: int, hours: int = 24) -> List[Dict]:
    """获取设备性能指标"""
    try:
        with db_manager.get_session() as session:
            time_threshold = datetime.datetime.utcnow() - datetime.timedelta(
                hours=hours
            )
            metrics = (
                session.query(DeviceMetric)
                .filter(
                    DeviceMetric.device_id == device_id,
                    DeviceMetric.collected_at >= time_threshold,
                )
                .order_by(DeviceMetric.collected_at.desc())
                .all()
            )

            return [
                {
                    "type": metric.metric_type,
                    "value": metric.value,
                    "time": metric.collected_at.isoformat(),
                }
                for metric in metrics
            ]
    except Exception as e:
        logger.error(f"Failed to get device metrics: {e}")
        return []


def get_device_tasks(device_id: int, limit: int = 10) -> List[Dict]:
    """获取设备相关任务"""
    try:
        with db_manager.get_session() as session:
            tasks = (
                session.query(Task)
                .filter(Task.device_id == device_id)
                .order_by(Task.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": task.id,
                    "name": task.name,
                    "type": task.type,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "creator": (
                        {
                            "name": task.creator.name,
                            "username": task.creator.username,
                        }
                        if task.creator
                        else None
                    ),
                }
                for task in tasks
            ]
    except Exception as e:
        logger.error(f"Failed to get device tasks: {e}")
        return []


async def update_device_config(device_id: str, config: Dict):
    """更新设备配置"""
    try:
        with db_manager.get_session() as session:
            device = session.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return False

            device.config = config
            device.updated_at = datetime.datetime.utcnow()
            session.commit()

            # 创建配置更新任务
            task = Task(
                name=f"更新设备 {device.name} 配置",
                type="config",
                status="pending",
                priority=2,  # 高优先级
                params={"config": config},
                device_id=device.id,
                creator_id=session_info.user.get("id"),
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            session.add(task)
            session.commit()

            return True
    except Exception as e:
        logger.error(f"Failed to update device config: {e}")
        return False


async def device_detail(device_id: str):
    """设备详情页面"""
    set_env(title="设备详情")

    # 页面样式
    style = """
    <style>
        .device-detail {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .detail-header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .device-name {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .device-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            margin-left: 10px;
        }
        .status-online {
            background: #dcfce7;
            color: #16a34a;
        }
        .status-offline {
            background: #fee2e2;
            color: #dc2626;
        }
        .status-error {
            background: #fef3c7;
            color: #d97706;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .detail-card {
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
        }
        .info-item {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            font-size: 14px;
        }
        .info-label {
            color: #666;
        }
        .info-value {
            color: #2c3e50;
            font-weight: 500;
        }
        .metric-chart {
            width: 100%;
            height: 300px;
            margin-top: 20px;
        }
        .task-list {
            margin-top: 20px;
        }
        .task-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }
        .task-item:last-child {
            border-bottom: none;
        }
        .task-info {
            flex: 1;
        }
        .task-name {
            font-weight: 500;
            color: #2c3e50;
        }
        .task-meta {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .task-status {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            margin-left: 10px;
        }
        .config-editor {
            width: 100%;
            height: 300px;
            font-family: monospace;
            margin-top: 10px;
            padding: 10px;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
        }
        .action-button {
            padding: 8px 16px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
            margin-top: 10px;
        }
        .save-button {
            background: #3b82f6;
            color: white;
        }
        .save-button:hover {
            background: #2563eb;
        }
    </style>
    """

    # 获取设备信息
    try:
        with db_manager.get_session() as session:
            device = session.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                put_error("设备不存在")
                return

            # 获取性能指标
            metrics = get_device_metrics(device.id)

            # 获取相关任务
            tasks = get_device_tasks(device.id)

            # 渲染页面
            clear()
            put_html(style)

            # 设备基本信息
            status_class = {
                "online": "status-online",
                "offline": "status-offline",
                "error": "status-error",
            }.get(device.status, "")

            put_html(
                f"""
            <div class="device-detail">
                <div class="detail-header">
                    <div class="device-name">
                        {device.name}
                        <span class="device-status \
                             {status_class}">{device.status}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">设备ID:</span>
                        <span class="info-value">{device.device_id}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">类型:</span>
                        <span class="info-value">{device.type}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">IP地址:</span>
                        <span class="info-value">{device.ip_address}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">最后心跳:</span>
                        <span \
                             class="info-value">{device.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S') if device.last_heartbeat else 'N/A'}</span>
                    </div>
                </div>
                
                <div class="detail-grid">
                    <!-- 性能监控 -->
                    <div class="detail-card">
                        <div class="card-title">性能监控</div>
                        <div id="metrics-chart" class="metric-chart"></div>
                    </div>
                    
                    <!-- 设备配置 -->
                    <div class="detail-card">
                        <div class="card-title">设备配置</div>
                        <textarea id="config-editor" \
                             class="config-editor">{json.dumps(device.config, \
                                  indent=2)}</textarea>
                        <button class="action-button save-button" \
                             onclick="saveConfig()">保存配置</button>
                    </div>
                </div>
                
                <!-- 任务列表 -->
                <div class="detail-card">
                    <div class="card-title">相关任务</div>
                    <div class="task-list">
            """
            )

            for task in tasks:
                status_class = {
                    "pending": "status-pending",
                    "running": "status-running",
                    "completed": "status-completed",
                    "failed": "status-failed",
                }.get(task["status"], "")

                put_html(
                    f"""
                    <div class="task-item">
                        <div class="task-info">
                            <div class="task-name">{task['name']}</div>
                            <div class="task-meta">
                                {task['type']} | 
                                创建者: {task['creator']['name'] if task['creator'] else \
                                     'N/A'} | 
                                创建时间: \
                                     {datetime.datetime.fromisoformat(task['created_at']).strftime('%Y-%m-%d %H:%M:%S')}
                            </div>
                        </div>
                        <span class="task-status {status_class}">{task['status']}</span>
                    </div>
                """
                )

            # 添加图表和交互脚本
            put_html(
                f"""
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script>
                // 性能指标图表
                const metrics = {json.dumps(metrics)};
                const metricTypes = [...new Set(metrics.map(m => m.type))];
                
                metricTypes.forEach(type => {{
                    const data = metrics.filter(m => m.type === type);
                    const trace = {{
                        x: data.map(d => d.time),
                        y: data.map(d => d.value.value),
                        type: 'scatter',
                        name: type
                    }};
                    
                    Plotly.newPlot(`metrics-chart-${{type}}`, [trace], {{
                        title: `${{type}} 使用率`,
                        xaxis: {{ title: '时间' }},
                        yaxis: {{ title: '使用率 (%)' }}
                    }});
                }});
                
                // 配置保存
                function saveConfig() {{
                    try {{
                        const config = \
                             JSON.parse(document.getElementById('config-editor').value);
                        pywebio.call_js_function('update_device_config', '{device_id}', \
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
                             config);
                    }} catch (e) {{
                        alert('配置格式无效，请检查JSON格式');
                    }}
                }}
                
                // WebSocket连接
                const ws = new WebSocket(`ws://${{window.location.host}}/ws/device/{device_id}`);
                ws.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    if (data.type === 'metric') {{
                        // 更新性能图表
                        const trace = {{
                            x: [data.time],
                            y: [data.value.value]
                        }};
                        Plotly.extendTraces(
                            `metrics-chart-${{data.metric_type}}`,
                            trace,
                            [0]
                        )
                    }} else if (data.type === 'status') {{
                        // 更新设备状态
                        document.querySelector('.device-status').className = 
                            `device-status status-${{data.status}}`;
                        document.querySelector('.device-status').textContent = \
                             data.status;
                    }}
                }};
            </script>
            """
            )

    except Exception as e:
        logger.error(f"Failed to load device detail: {e}")
        put_error("加载设备详情失败")


if __name__ == "__main__":
    device_detail("test-device-001")
