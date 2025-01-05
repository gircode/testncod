"""基础模型"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declared_attr


class BaseModel:
    """基础模型类"""

    @declared_attr
    def __tablename__(cls) -> str:
        """表名默认为类名的小写形式"""
        return cls.__name__.lower()

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        """模型的字符串表示"""
        attrs = []
        for key in self.__table__.columns.keys():
            if key not in {"created_at", "updated_at"}:
                value = getattr(self, key)
                attrs.append(f"{key}={value}")
        return f"<{self.__class__.__name__} {' '.join(attrs)}>"
