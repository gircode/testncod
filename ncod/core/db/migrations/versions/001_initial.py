"""初始迁移

Revision ID: 001
Revises: 
Create Date: 2024-03-20 10:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建组织表
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=200)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建部门表
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer()),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["departments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建用户表
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=100), nullable=False),
        sa.Column("department_id", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_temporary", sa.Boolean(), nullable=False),
        sa.Column("expire_date", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    # 创建设备表
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("group_id", sa.Integer()),
        sa.Column("ip_address", sa.String(length=15)),
        sa.Column("mac_address", sa.String(length=17)),
        sa.Column("status", sa.String(length=20)),
        sa.Column("last_online", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建USB端口表
    op.create_table(
        "usb_ports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("port_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20)),
        sa.Column("current_user_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["current_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建设备授权表
    op.create_table(
        "device_authorizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("group_ids", postgresql.JSONB(), nullable=False),
        sa.Column("department_ids", postgresql.JSONB(), nullable=False),
        sa.Column("user_ids", postgresql.JSONB(), nullable=False),
        sa.Column("expire_date", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建端口队列表
    op.create_table(
        "port_queues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("port_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20)),
        sa.Column("request_time", sa.DateTime(), nullable=False),
        sa.Column("start_time", sa.DateTime()),
        sa.Column("end_time", sa.DateTime()),
        sa.Column("estimated_duration", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["port_id"],
            ["usb_ports.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # 按照相反的顺序删除表
    op.drop_table("port_queues")
    op.drop_table("device_authorizations")
    op.drop_table("usb_ports")
    op.drop_table("devices")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("groups")
