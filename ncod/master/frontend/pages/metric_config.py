"""Metric Config模块"""

import json

from database import db_manager
from models.user import AlertRule, Device, MetricDefinition
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_js
from services.cache import cache


async def metric_config():
    """自定义监控指标配置页面"""
    put_markdown("## 自定义监控指标配置")

    # 指标定义表单
    async def create_metric_definition():
        data = await input_group(
            "创建指标定义",
            [
                input("指标名称", name="name", required=True),
                select(
                    "指标类型", name="type", options=["counter", "gauge", "histogram"]
                ),
                input("单位", name="unit", required=True),
                textarea("描述", name="description"),
                textarea(
                    "收集脚本",
                    name="collection_script",
                    placeholder="Python脚本,支持自定义数据收集逻辑",
                ),
                input("收集间隔(秒)", name="interval", type=NUMBER, value=60),
                checkbox("启用聚合", name="enable_aggregation", options=["是"]),
                textarea(
                    "聚合规则",
                    name="aggregation_rules",
                    placeholder='{"avg": "5m", "max": "1h"}',
                ),
            ],
        )

        with db_manager.get_session() as session:
            definition = MetricDefinition(
                name=data["name"],
                type=data["type"],
                unit=data["unit"],
                description=data["description"],
                collection_script=data["collection_script"],
                collection_interval=data["interval"],
                enable_aggregation=bool(data["enable_aggregation"]),
                aggregation_rules=json.loads(data["aggregation_rules"] or "{}"),
            )
            session.add(definition)
            session.commit()

        toast("指标定义创建成功")
        await show_metric_definitions()

    # 告警规则表单
    async def create_alert_rule():
        with db_manager.get_session() as session:
            metrics = session.query(MetricDefinition).all()
            metric_options = [(m.id, m.name) for m in metrics]

        data = await input_group(
            "创建告警规则",
            [
                select("指标", name="metric_id", options=metric_options),
                select("条件", name="condition", options=[">", ">=", "<", "<=", "=="]),
                input("阈值", name="threshold", type=FLOAT),
                select(
                    "严重程度", name="severity", options=["critical", "warning", "info"]
                ),
                textarea("描述", name="description"),
                input("持续时间(秒)", name="duration", type=NUMBER, value=300),
                checkbox("启用", name="enabled", options=["是"]),
            ],
        )

        with db_manager.get_session() as session:
            rule = AlertRule(
                metric_id=data["metric_id"],
                condition=data["condition"],
                threshold=data["threshold"],
                severity=data["severity"],
                description=data["description"],
                duration=data["duration"],
                enabled=bool(data["enabled"]),
            )
            session.add(rule)
            session.commit()

        toast("告警规则创建成功")
        await show_alert_rules()

    # 显示指标定义列表
    async def show_metric_definitions():
        with db_manager.get_session() as session:
            definitions = session.query(MetricDefinition).all()

        if not definitions:
            put_text("暂无指标定义")
            return

        # 构建表格数据
        headers = ["名称", "类型", "单位", "收集间隔", "聚合", "操作"]
        rows = []
        for d in definitions:
            rows.append(
                [
                    d.name,
                    d.type,
                    d.unit,
                    f"{d.collection_interval}秒",
                    "是" if d.enable_aggregation else "否",
                    put_buttons(
                        ["编辑", "删除"],
                        onclick=[
                            lambda d=d: edit_definition(d.id),
                            lambda d=d: delete_definition(d.id),
                        ],
                    ),
                ]
            )

        put_table(rows, headers)

    # 显示告警规则列表
    async def show_alert_rules():
        with db_manager.get_session() as session:
            rules = session.query(AlertRule).all()

        if not rules:
            put_text("暂无告警规则")
            return

        # 构建表格数据
        headers = ["指标", "条件", "阈值", "严重程度", "持续时间", "状态", "操作"]
        rows = []
        for r in rules:
            rows.append(
                [
                    r.metric.name,
                    r.condition,
                    r.threshold,
                    r.severity,
                    f"{r.duration}秒",
                    "启用" if r.enabled else "禁用",
                    put_buttons(
                        ["编辑", "删除"],
                        onclick=[
                            lambda r=r: edit_rule(r.id),
                            lambda r=r: delete_rule(r.id),
                        ],
                    ),
                ]
            )

        put_table(rows, headers)

    # 编辑指标定义
    async def edit_definition(definition_id):
        with db_manager.get_session() as session:
            definition = session.query(MetricDefinition).get(definition_id)
            if not definition:
                return

            data = await input_group(
                "编辑指标定义",
                [
                    input("指标名称", name="name", value=definition.name),
                    select(
                        "指标类型",
                        name="type",
                        value=definition.type,
                        options=["counter", "gauge", "histogram"],
                    ),
                    input("单位", name="unit", value=definition.unit),
                    textarea("描述", name="description", value=definition.description),
                    textarea(
                        "收集脚本",
                        name="collection_script",
                        value=definition.collection_script,
                    ),
                    input(
                        "收集间隔(秒)",
                        name="interval",
                        type=NUMBER,
                        value=definition.collection_interval,
                    ),
                    checkbox(
                        "启用聚合",
                        name="enable_aggregation",
                        value=["是"] if definition.enable_aggregation else [],
                    ),
                    textarea(
                        "聚合规则",
                        name="aggregation_rules",
                        value=json.dumps(definition.aggregation_rules),
                    ),
                ],
            )

            definition.name = data["name"]
            definition.type = data["type"]
            definition.unit = data["unit"]
            definition.description = data["description"]
            definition.collection_script = data["collection_script"]
            definition.collection_interval = data["interval"]
            definition.enable_aggregation = bool(data["enable_aggregation"])
            definition.aggregation_rules = json.loads(data["aggregation_rules"])

            session.commit()

        toast("指标定义更新成功")
        await show_metric_definitions()

    # 编辑告警规则
    async def edit_rule(rule_id):
        with db_manager.get_session() as session:
            rule = session.query(AlertRule).get(rule_id)
            if not rule:
                return

            metrics = session.query(MetricDefinition).all()
            metric_options = [(m.id, m.name) for m in metrics]

            data = await input_group(
                "编辑告警规则",
                [
                    select(
                        "指标",
                        name="metric_id",
                        value=rule.metric_id,
                        options=metric_options,
                    ),
                    select(
                        "条件",
                        name="condition",
                        value=rule.condition,
                        options=[">", ">=", "<", "<=", "=="],
                    ),
                    input("阈值", name="threshold", type=FLOAT, value=rule.threshold),
                    select(
                        "严重程度",
                        name="severity",
                        value=rule.severity,
                        options=["critical", "warning", "info"],
                    ),
                    textarea("描述", name="description", value=rule.description),
                    input(
                        "持续时间(秒)",
                        name="duration",
                        type=NUMBER,
                        value=rule.duration,
                    ),
                    checkbox(
                        "启用", name="enabled", value=["是"] if rule.enabled else []
                    ),
                ],
            )

            rule.metric_id = data["metric_id"]
            rule.condition = data["condition"]
            rule.threshold = data["threshold"]
            rule.severity = data["severity"]
            rule.description = data["description"]
            rule.duration = data["duration"]
            rule.enabled = bool(data["enabled"])

            session.commit()

        toast("告警规则更新成功")
        await show_alert_rules()

    # 删除指标定义
    async def delete_definition(definition_id):
        if await actions("确认删除该指标定义?", ["确认", "取消"]) == "确认":
            with db_manager.get_session() as session:
                definition = session.query(MetricDefinition).get(definition_id)
                if definition:
                    session.delete(definition)
                    session.commit()

            toast("指标定义已删除")
            await show_metric_definitions()

    # 删除告警规则
    async def delete_rule(rule_id):
        if await actions("确认删除该告警规则?", ["确认", "取消"]) == "确认":
            with db_manager.get_session() as session:
                rule = session.query(AlertRule).get(rule_id)
                if rule:
                    session.delete(rule)
                    session.commit()

            toast("告警规则已删除")
            await show_alert_rules()

    # 页面布局
    put_row(
        [
            put_column(
                [
                    put_markdown("### 指标定义"),
                    put_button("创建指标定义", onclick=create_metric_definition),
                    put_scope("metric_definitions", []),
                ]
            ),
            put_column(
                [
                    put_markdown("### 告警规则"),
                    put_button("创建告警规则", onclick=create_alert_rule),
                    put_scope("alert_rules", []),
                ]
            ),
        ]
    )

    # 初始显示数据
    await show_metric_definitions()
    await show_alert_rules()
