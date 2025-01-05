import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, SystemLog
from .utils.logger import get_logger

logger = get_logger(__name__)


class LogManager:
    _instance: Optional['LogManager'] = None
    
    def __new__(cls) -> 'LogManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def add_log(
        self,
        level: str,
        module: str,
        message: str,
        user_id: Optional[int] = None
    ) -> bool:
        """添加日志记录"""
        try:
            log = SystemLog(
                level=level,
                module=module,
                message=message,
                user_id=user_id,
                created_at=datetime.now()
            )
            
            db.session.add(log)
            db.session.commit()
            
            logger.debug(
                f"Log added: [{level}] {module} - {message}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to add log: {e}")
            db.session.rollback()
            return False
    
    def get_recent_logs(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        module: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取最近的日志记录"""
        try:
            query = SystemLog.query
            
            if level:
                query = query.filter(SystemLog.level == level)
            if module:
                query = query.filter(SystemLog.module == module)
            if user_id:
                query = query.filter(SystemLog.user_id == user_id)
                
            logs = query.order_by(
                desc(SystemLog.created_at)
            ).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [log.to_dict() for log in logs])
            
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    def search_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[str] = None,
        module: Optional[str] = None,
        user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """搜索日志记录"""
        try:
            query = SystemLog.query
            
            if start_time:
                query = query.filter(SystemLog.created_at >= start_time)
            if end_time:
                query = query.filter(SystemLog.created_at <= end_time)
            if level:
                query = query.filter(SystemLog.level == level)
            if module:
                query = query.filter(SystemLog.module == module)
            if user_id:
                query = query.filter(SystemLog.user_id == user_id)
            if keyword:
                query = query.filter(SystemLog.message.ilike(f"%{keyword}%"))
                
            logs = query.order_by(
                desc(SystemLog.created_at)
            ).offset(offset).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [log.to_dict() for log in logs])
            
        except Exception as e:
            logger.error(f"Failed to search logs: {e}")
            return []
    
    def clean_old_logs(self, days: int = 30) -> bool:
        """清理旧日志记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            SystemLog.query.filter(
                SystemLog.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            logger.info(f"Cleaned logs older than {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean old logs: {e}")
            db.session.rollback()
            return False
    
    def export_logs(
        self,
        file_path: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[str] = None,
        module: Optional[str] = None
    ) -> bool:
        """导出日志记录到文件"""
        try:
            query = SystemLog.query
            
            if start_time:
                query = query.filter(SystemLog.created_at >= start_time)
            if end_time:
                query = query.filter(SystemLog.created_at <= end_time)
            if level:
                query = query.filter(SystemLog.level == level)
            if module:
                query = query.filter(SystemLog.module == module)
                
            logs = query.order_by(SystemLog.created_at).all()
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for log in logs:
                    f.write(
                        f"[{log.created_at}] [{log.level}] "
                        f"{log.module} - {log.message}\n"
                    )
                    
            logger.info(f"Logs exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return False
    
    def get_log_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            query = SystemLog.query
            
            if start_time:
                query = query.filter(SystemLog.created_at >= start_time)
            if end_time:
                query = query.filter(SystemLog.created_at <= end_time)
                
            total_count = query.count()
            level_counts: Dict[str, int] = {}
            module_counts: Dict[str, int] = {}
            
            for log in query.all():
                level_counts[log.level] = level_counts.get(log.level, 0) + 1
                module_counts[log.module] = module_counts.get(log.module, 0) + 1
                
            return {
                'total_count': total_count,
                'level_counts': level_counts,
                'module_counts': module_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}")
            return {
                'total_count': 0,
                'level_counts': {},
                'module_counts': {}
            } 