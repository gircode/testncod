"""
审计日志模型
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, select, update
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base_class import Base
from .models import User

logger = logging.getLogger(__name__)


class AuditLog(Base):
    """审计日志"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(200))

    # 关系
    user: Mapped[User] = relationship(back_populates="audit_logs")


class ConfigAudit(Base):
    """配置审计日志"""

    __tablename__ = "config_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # create, update, delete
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    old_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # 旧元数据
    new_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # 新元数据
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(200))

    # 关系
    user: Mapped[User] = relationship(back_populates="config_audits")


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, db_session):
        self.db_session = db_session

    async def log_config_change(
        self,
        config_key: str,
        action: str,
        user_id: int,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        old_metadata: Optional[Dict[str, Any]] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """记录配置变更"""
        try:
            audit = ConfigAudit(
                config_key=config_key,
                action=action,
                old_value=old_value,
                new_value=new_value,
                old_metadata=old_metadata,
                new_metadata=new_metadata,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db_session.add(audit)
            await self.db_session.commit()
            logger.info(f"配置审计日志记录成功: {config_key}")
        except Exception as e:
            logger.error(f"配置审计日志记录失败: {str(e)}")
            await self.db_session.rollback()
            raise

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: int,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """记录操作日志"""
        try:
            audit = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db_session.add(audit)
            await self.db_session.commit()
            logger.info(f"操作审计日志记录成功: {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"操作审计日志记录失败: {str(e)}")
            await self.db_session.rollback()
            raise

    async def get_config_audit_logs(
        self,
        config_key: Optional[str] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ConfigAudit]:
        """获取配置审计日志"""
        try:
            query = select(ConfigAudit)
            if config_key:
                query = query.filter(ConfigAudit.config_key == config_key)
            if user_id:
                query = query.filter(ConfigAudit.user_id == user_id)
            if action:
                query = query.filter(ConfigAudit.action == action)
            if start_time:
                query = query.filter(ConfigAudit.timestamp >= start_time)
            if end_time:
                query = query.filter(ConfigAudit.timestamp <= end_time)

            query = query.order_by(ConfigAudit.timestamp.desc())
            query = query.offset(skip).limit(limit)

            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取配置审计日志失败: {str(e)}")
            raise

    async def get_audit_logs(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取操作审计日志"""
        try:
            query = select(AuditLog)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            if resource_id:
                query = query.filter(AuditLog.resource_id == resource_id)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)
            if start_time:
                query = query.filter(AuditLog.timestamp >= start_time)
            if end_time:
                query = query.filter(AuditLog.timestamp <= end_time)

            query = query.order_by(AuditLog.timestamp.desc())
            query = query.offset(skip).limit(limit)

            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取操作审计日志失败: {str(e)}")
            raise
