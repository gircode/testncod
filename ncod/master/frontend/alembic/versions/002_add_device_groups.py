"""add device groups

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
    # 创建设备组表
    op.create_table(
        "device_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建设备组关联表
    op.create_table(
        "device_group_association",
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["device_groups.id"],
        ),
    )

    # 更新设备表的列
    op.alter_column(
        "devices",
        "device_id",
        existing_type=sa.String(length=50),
        type_=sa.String(length=100),
    )
    op.alter_column(
        "devices",
        "type",
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
    )
    op.alter_column(
        "devices",
        "ip_address",
        existing_type=sa.String(length=45),
        type_=sa.String(length=50),
    )

    # 修改设备指标表的value列类型
    op.alter_column(
        "device_metrics", "value", existing_type=sa.JSON(), type_=sa.String(length=100)
    )

    # 简化任务表
    op.drop_column("tasks", "priority")
    op.drop_column("tasks", "params")
    op.drop_column("tasks", "error_message")
    op.drop_column("tasks", "started_at")
    op.drop_column("tasks", "completed_at")
    op.alter_column("tasks", "name", existing_type=sa.String(length=100), nullable=True)


def downgrade():
    # 删除设备组关联表
    op.drop_table("device_group_association")

    # 删除设备组表
    op.drop_table("device_groups")

    # 恢复设备表的列
    op.alter_column(
        "devices",
        "device_id",
        existing_type=sa.String(length=100),
        type_=sa.String(length=50),
    )
    op.alter_column(
        "devices",
        "type",
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
    )
    op.alter_column(
        "devices",
        "ip_address",
        existing_type=sa.String(length=50),
        type_=sa.String(length=45),
    )

    # 恢复设备指标表的value列类型
    op.alter_column(
        "device_metrics", "value", existing_type=sa.String(length=100), type_=sa.JSON()
    )

    # 恢复任务表
    op.add_column("tasks", sa.Column("priority", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("params", sa.JSON(), nullable=True))
    op.add_column(
        "tasks", sa.Column("error_message", sa.String(length=500), nullable=True)
    )
    op.add_column("tasks", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("tasks", sa.Column("completed_at", sa.DateTime(), nullable=True))
    op.alter_column(
        "tasks", "name", existing_type=sa.String(length=100), nullable=False
    )
