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
    # 创建监控指标表
    op.create_table(
        "monitormetric",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_type", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index("ix_monitormetric_metric_type", "monitormetric", ["metric_type"])
    op.create_index("ix_monitormetric_timestamp", "monitormetric", ["timestamp"])

    op.create_index("ix_monitoralert_alert_type", "monitoralert", ["alert_type"])
    op.create_index("ix_monitoralert_severity", "monitoralert", ["severity"])
    op.create_index("ix_monitoralert_status", "monitoralert", ["status"])
    op.create_index("ix_monitoralert_created_at", "monitoralert", ["created_at"])


def downgrade():
    # 删除索引
    op.drop_index("ix_monitoralert_created_at", "monitoralert")
    op.drop_index("ix_monitoralert_status", "monitoralert")
    op.drop_index("ix_monitoralert_severity", "monitoralert")
    op.drop_index("ix_monitoralert_alert_type", "monitoralert")

    op.drop_index("ix_monitormetric_timestamp", "monitormetric")
    op.drop_index("ix_monitormetric_metric_type", "monitormetric")

    # 删除表
    op.drop_table("monitoralert")
    op.drop_table("monitormetric")
