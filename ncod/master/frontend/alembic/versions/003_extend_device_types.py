"""extend device types

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # 添加新的设备字段
    op.add_column("devices", sa.Column("subtype", sa.String(length=50), nullable=True))
    op.add_column(
        "devices", sa.Column("mac_address", sa.String(length=17), nullable=True)
    )
    op.add_column(
        "devices", sa.Column("manufacturer", sa.String(length=100), nullable=True)
    )
    op.add_column("devices", sa.Column("model", sa.String(length=100), nullable=True))
    op.add_column("devices", sa.Column("os_type", sa.String(length=50), nullable=True))
    op.add_column(
        "devices", sa.Column("os_version", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "devices", sa.Column("firmware_version", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "devices", sa.Column("serial_number", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "devices", sa.Column("location", sa.String(length=200), nullable=True)
    )
    op.add_column("devices", sa.Column("capabilities", sa.JSON(), nullable=True))
    op.add_column("devices", sa.Column("monitoring_config", sa.JSON(), nullable=True))
    op.add_column("devices", sa.Column("backup_config", sa.JSON(), nullable=True))
    op.add_column("devices", sa.Column("security_config", sa.JSON(), nullable=True))
    op.add_column("devices", sa.Column("last_backup", sa.DateTime(), nullable=True))
    op.add_column(
        "devices", sa.Column("last_security_scan", sa.DateTime(), nullable=True)
    )

    # 创建设备备份表
    op.create_table(
        "device_backups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False
        ),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("backup_path", sa.String(length=500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建安全扫描表
    op.create_table(
        "security_scans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False
        ),
        sa.Column("scan_type", sa.String(length=50), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("findings", sa.JSON(), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建告警表
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False
        ),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="active"
        ),
        sa.Column(
            "acknowledged_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 更新设备指标表
    op.add_column(
        "device_metrics", sa.Column("metric_name", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "device_metrics", sa.Column("unit", sa.String(length=20), nullable=True)
    )
    op.add_column("device_metrics", sa.Column("tags", sa.JSON(), nullable=True))


def downgrade():
    # 删除告警表
    op.drop_table("alerts")

    # 删除安全扫描表
    op.drop_table("security_scans")

    # 删除设备备份表
    op.drop_table("device_backups")

    # 删除设备新增字段
    op.drop_column("devices", "subtype")
    op.drop_column("devices", "mac_address")
    op.drop_column("devices", "manufacturer")
    op.drop_column("devices", "model")
    op.drop_column("devices", "os_type")
    op.drop_column("devices", "os_version")
    op.drop_column("devices", "firmware_version")
    op.drop_column("devices", "serial_number")
    op.drop_column("devices", "location")
    op.drop_column("devices", "capabilities")
    op.drop_column("devices", "monitoring_config")
    op.drop_column("devices", "backup_config")
    op.drop_column("devices", "security_config")
    op.drop_column("devices", "last_backup")
    op.drop_column("devices", "last_security_scan")

    # 删除设备指标新增字段
    op.drop_column("device_metrics", "metric_name")
    op.drop_column("device_metrics", "unit")
    op.drop_column("device_metrics", "tags")
