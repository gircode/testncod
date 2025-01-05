"""add monitor tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-20 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # 创建设备性能指标表
    op.create_table(
        "device_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("metric_type", sa.String(length=50), nullable=True),
        sa.Column("value", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("collected_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建告警规则表
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("metric_type", sa.String(length=50), nullable=True),
        sa.Column("condition", sa.String(length=10), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建系统告警表
    op.create_table(
        "system_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=True),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["alert_rules.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index(
        "ix_device_metrics_collected_at",
        "device_metrics",
        ["collected_at"],
        unique=False,
    )
    op.create_index(
        "ix_device_metrics_device_id", "device_metrics", ["device_id"], unique=False
    )
    op.create_index(
        "ix_device_metrics_metric_type", "device_metrics", ["metric_type"], unique=False
    )
    op.create_index(
        "ix_alert_rules_metric_type", "alert_rules", ["metric_type"], unique=False
    )
    op.create_index(
        "ix_system_alerts_created_at", "system_alerts", ["created_at"], unique=False
    )
    op.create_index(
        "ix_system_alerts_device_id", "system_alerts", ["device_id"], unique=False
    )
    op.create_index(
        "ix_system_alerts_rule_id", "system_alerts", ["rule_id"], unique=False
    )
    op.create_index(
        "ix_system_alerts_status", "system_alerts", ["status"], unique=False
    )


def downgrade():
    # 删除索引
    op.drop_index("ix_system_alerts_status", table_name="system_alerts")
    op.drop_index("ix_system_alerts_rule_id", table_name="system_alerts")
    op.drop_index("ix_system_alerts_device_id", table_name="system_alerts")
    op.drop_index("ix_system_alerts_created_at", table_name="system_alerts")
    op.drop_index("ix_alert_rules_metric_type", table_name="alert_rules")
    op.drop_index("ix_device_metrics_metric_type", table_name="device_metrics")
    op.drop_index("ix_device_metrics_device_id", table_name="device_metrics")
    op.drop_index("ix_device_metrics_collected_at", table_name="device_metrics")

    # 删除表
    op.drop_table("system_alerts")
    op.drop_table("alert_rules")
    op.drop_table("device_metrics")
