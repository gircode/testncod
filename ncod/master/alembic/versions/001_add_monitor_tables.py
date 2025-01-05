"""
添加监控相关表
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_add_monitor_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建从节点表
    op.create_table(
        "slavenode",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="unknown"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 创建监控指标表
    op.create_table(
        "monitormetric",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_type", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("node_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["node_id"], ["slavenode.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建监控告警表
    op.create_table(
        "monitoralert",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("node_id", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["node_id"], ["slavenode.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index("ix_monitormetric_metric_type", "monitormetric", ["metric_type"])
    op.create_index("ix_monitormetric_timestamp", "monitormetric", ["timestamp"])
    op.create_index("ix_monitormetric_node_id", "monitormetric", ["node_id"])

    op.create_index("ix_monitoralert_alert_type", "monitoralert", ["alert_type"])
    op.create_index("ix_monitoralert_severity", "monitoralert", ["severity"])
    op.create_index("ix_monitoralert_status", "monitoralert", ["status"])
    op.create_index("ix_monitoralert_node_id", "monitoralert", ["node_id"])
    op.create_index("ix_monitoralert_created_at", "monitoralert", ["created_at"])


def downgrade():
    # 删除索引
    op.drop_index("ix_monitoralert_created_at", "monitoralert")
    op.drop_index("ix_monitoralert_node_id", "monitoralert")
    op.drop_index("ix_monitoralert_status", "monitoralert")
    op.drop_index("ix_monitoralert_severity", "monitoralert")
    op.drop_index("ix_monitoralert_alert_type", "monitoralert")

    op.drop_index("ix_monitormetric_node_id", "monitormetric")
    op.drop_index("ix_monitormetric_timestamp", "monitormetric")
    op.drop_index("ix_monitormetric_metric_type", "monitormetric")

    # 删除表
    op.drop_table("monitoralert")
    op.drop_table("monitormetric")
    op.drop_table("slavenode")
