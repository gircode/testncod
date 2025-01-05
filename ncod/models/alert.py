"""告警模型模块"""

# 标准库导入
from datetime import datetime
from typing import Dict, Optional

# 第三方库导入
from sqlalchemy import Column, DateTime, Integer, String, JSON
from sqlalchemy.orm import relationship

# 本地导入
from ncod.core.db import Base


class Alert(Base):
    """告警模型"""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    metadata = Column(JSON)
