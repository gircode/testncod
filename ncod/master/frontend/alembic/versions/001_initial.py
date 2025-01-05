"""initial

Revision ID: 001
Revises: 
Create Date: 2024-01-10 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建用户表
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password", sa.String(length=256), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "permissions", postgresql.JSON(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("password_changed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("lockout_until", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    # 创建会话表
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("user_agent", sa.String(length=200)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_remembered", sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    # 创建密码重置表
    op.create_table(
        "password_resets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    # 创建审计日志表
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer()),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("details", postgresql.JSON(astext_type=sa.Text())),
        sa.Column("ip_address", sa.String(length=45)),
        sa.Column("user_agent", sa.String(length=200)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])
    op.create_index("ix_password_resets_user_id", "password_resets", ["user_id"])
    op.create_index("ix_password_resets_expires_at", "password_resets", ["expires_at"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    op.drop_index("ix_audit_logs_created_at")
    op.drop_index("ix_audit_logs_user_id")
    op.drop_index("ix_password_resets_expires_at")
    op.drop_index("ix_password_resets_user_id")
    op.drop_index("ix_sessions_expires_at")
    op.drop_index("ix_sessions_user_id")
    op.drop_index("ix_users_username")
    op.drop_index("ix_users_email")

    op.drop_table("audit_logs")
    op.drop_table("password_resets")
    op.drop_table("sessions")
    op.drop_table("users")
