"""add rbac tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # 创建角色表
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 创建权限表
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("action", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )

    # 创建角色-权限关联表
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("permission_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
    )

    # 创建用户-角色关联表
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
    )

    # 创建索引
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index(
        "ix_permissions_resource_type", "permissions", ["resource_type"], unique=False
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.create_index(
        "ix_role_permissions_role_id", "role_permissions", ["role_id"], unique=False
    )
    op.create_index(
        "ix_role_permissions_permission_id",
        "role_permissions",
        ["permission_id"],
        unique=False,
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"], unique=False)
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], unique=False)


def downgrade():
    # 删除索引
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_index("ix_permissions_resource_type", table_name="permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")

    # 删除表
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
