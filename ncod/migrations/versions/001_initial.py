"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建用户表
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("organization", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", "disabled", name="user_status"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
        ),
    )

    # 创建MAC地址表
    op.create_table(
        "mac_addresses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=17), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("last_used", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("address"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
    )

    # 创建从服务器表
    op.create_table(
        "slaves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("host", "port"),
    )

    # 创建设备表
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slave_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("device_type", sa.String(length=50), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["slave_id"],
            ["slaves.id"],
        ),
    )

    # 创建设备指标表
    op.create_table(
        "device_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("is_connected", sa.Boolean(), nullable=False),
        sa.Column("usage_duration", sa.Float(), nullable=False),
        sa.Column("bandwidth_usage", sa.Float(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
        ),
    )

    # 创建从服务器指标表
    op.create_table(
        "slave_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slave_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("is_healthy", sa.Boolean(), nullable=False),
        sa.Column("device_count", sa.Integer(), nullable=False),
        sa.Column("cpu_usage", sa.Float(), nullable=False),
        sa.Column("memory_usage", sa.Float(), nullable=False),
        sa.Column("network_tx", sa.Float(), nullable=False),
        sa.Column("network_rx", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["slave_id"],
            ["slaves.id"],
        ),
    )

    # 创建索引
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_mac_addresses_address", "mac_addresses", ["address"])
    op.create_index("ix_devices_serial_number", "devices", ["serial_number"])
    op.create_index("ix_device_metrics_timestamp", "device_metrics", ["timestamp"])
    op.create_index("ix_slave_metrics_timestamp", "slave_metrics", ["timestamp"])


def downgrade() -> None:
    # 删除索引
    op.drop_index("ix_slave_metrics_timestamp")
    op.drop_index("ix_device_metrics_timestamp")
    op.drop_index("ix_devices_serial_number")
    op.drop_index("ix_mac_addresses_address")
    op.drop_index("ix_users_email")
    op.drop_index("ix_users_username")

    # 删除表
    op.drop_table("slave_metrics")
    op.drop_table("device_metrics")
    op.drop_table("devices")
    op.drop_table("slaves")
    op.drop_table("mac_addresses")
    op.drop_table("users")
