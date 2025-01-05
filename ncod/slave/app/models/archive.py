"""
归档数据模型
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String

from ..db.base_class import Base


class MetricArchive(Base):
    """指标归档表"""

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String, index=True)  # 指标类型
    start_time = Column(DateTime, index=True)  # 开始时间
    end_time = Column(DateTime, index=True)  # 结束时间
    min_value = Column(Float)  # 最小值
    max_value = Column(Float)  # 最大值
    avg_value = Column(Float)  # 平均值
    sample_count = Column(Integer)  # 样本数
    metadata = Column(JSON)  # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
