"""基准测试模型模块"""

# 标准库导入
from datetime import datetime
from typing import Dict, Optional

# 第三方库导入
from sqlalchemy import Column, DateTime, Float, Integer, String, JSON
from sqlalchemy.orm import relationship

# 本地导入
from ncod.core.db import Base


class Benchmark(Base):
    """基准测试模型"""

    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
