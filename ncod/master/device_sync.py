from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, Device, DeviceSync
from .utils.logger import get_logger
from .config_manager import ConfigManager
from .device_stats import DeviceStatsManager

logger = get_logger(__name__)
config = ConfigManager()
stats_manager = DeviceStatsManager()


class DeviceSyncManager:
    _instance: Optional['DeviceSyncManager'] = None
    
    def __new__(cls) -> 'DeviceSyncManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_sync_task(
        self,
        device_id: int,
        target_server: str,
        sync_type: str,
        priority: int = 0,
        retry_count: int = 3,
        timeout: int = 300
    ) -> Optional[Dict[str, Any]]:
        """创建同步任务"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 检查是否有正在进行的同步任务
            existing = DeviceSync.query.filter_by(
                device_id=device_id,
                status='pending'
            ).first()
            
            if existing:
                logger.error(
                    f"Sync task already exists: {device_id} -> {target_server}"
                )
                return cast(Dict[str, Any], existing.to_dict())
                
            # 创建同步任务
            sync_task = DeviceSync(
                device_id=device_id,
                target_server=target_server,
                sync_type=sync_type,
                priority=priority,
                retry_count=retry_count,
                timeout=timeout,
                status='pending',
                created_at=datetime.now()
            )
            
            db.session.add(sync_task)
            db.session.commit()
            
            logger.info(
                f"Sync task created: {device.name} -> {target_server}"
            )
            return cast(Dict[str, Any], sync_task.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to create sync task: {e}")
            db.session.rollback()
            return None
    
    def update_sync_status(
        self,
        task_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """更新同步状态"""
        try:
            sync_task = DeviceSync.query.get(task_id)
            if not sync_task:
                logger.error(f"Sync task not found: {task_id}")
                return False
                
            sync_task.status = status
            sync_task.error_message = error_message
            sync_task.updated_at = datetime.now()
            
            if status == 'completed':
                sync_task.completed_at = datetime.now()
                # 更新设备统计信息
                stats_manager.update_sync_stats(sync_task.device_id)
                
            db.session.commit()
            
            logger.info(f"Sync task updated: {task_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update sync status: {e}")
            db.session.rollback()
            return False
    
    def retry_sync_task(self, task_id: int) -> bool:
        """重试同步任务"""
        try:
            sync_task = DeviceSync.query.get(task_id)
            if not sync_task:
                logger.error(f"Sync task not found: {task_id}")
                return False
                
            if sync_task.retry_count <= 0:
                logger.error(f"No more retries allowed: {task_id}")
                return False
                
            sync_task.retry_count -= 1
            sync_task.status = 'pending'
            sync_task.error_message = None
            sync_task.updated_at = datetime.now()
            
            db.session.commit()
            
            logger.info(f"Sync task retried: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry sync task: {e}")
            db.session.rollback()
            return False
    
    def cancel_sync_task(self, task_id: int) -> bool:
        """取消同步任务"""
        try:
            sync_task = DeviceSync.query.get(task_id)
            if not sync_task:
                logger.error(f"Sync task not found: {task_id}")
                return False
                
            if sync_task.status not in ['pending', 'running']:
                logger.error(
                    f"Cannot cancel task in status: {sync_task.status}"
                )
                return False
                
            sync_task.status = 'cancelled'
            sync_task.updated_at = datetime.now()
            
            db.session.commit()
            
            logger.info(f"Sync task cancelled: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel sync task: {e}")
            db.session.rollback()
            return False
    
    def list_sync_tasks(
        self,
        device_id: Optional[int] = None,
        status: Optional[str] = None,
        target_server: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出同步任务"""
        try:
            query = DeviceSync.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if status:
                query = query.filter_by(status=status)
            if target_server:
                query = query.filter_by(target_server=target_server)
            if start_date:
                query = query.filter(DeviceSync.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceSync.created_at <= end_date)
                
            sync_tasks = query.order_by(
                desc(DeviceSync.created_at)
            ).offset(offset).limit(limit).all()
            
            return [
                cast(Dict[str, Any], task.to_dict()) for task in sync_tasks
            ]
            
        except Exception as e:
            logger.error(f"Failed to list sync tasks: {e}")
            return []
    
    def get_sync_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取同步摘要"""
        try:
            query = DeviceSync.query
            
            if start_date:
                query = query.filter(DeviceSync.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceSync.created_at <= end_date)
                
            # 总任务数
            total_tasks = query.count()
            
            # 按状态统计
            status_counts: Dict[str, int] = {}
            for status in ['pending', 'running', 'completed', 'failed', 'cancelled']:
                count = query.filter_by(status=status).count()
                status_counts[status] = count
                
            # 按服务器统计
            server_counts: Dict[str, int] = {}
            for server in query.with_entities(
                DeviceSync.target_server
            ).distinct().all():
                count = query.filter_by(target_server=server[0]).count()
                server_counts[server[0]] = count
                
            # 按设备统计
            device_counts: Dict[int, int] = {}
            for device_id in query.with_entities(
                DeviceSync.device_id
            ).distinct().all():
                count = query.filter_by(device_id=device_id[0]).count()
                device_counts[device_id[0]] = count
                
            # 计算平均重试次数
            retry_stats = db.session.query(
                db.func.avg(DeviceSync.retry_count)
            ).scalar()
            avg_retries = float(retry_stats) if retry_stats else 0.0
                
            return {
                'total_tasks': total_tasks,
                'status_counts': status_counts,
                'server_counts': server_counts,
                'device_counts': device_counts,
                'avg_retries': avg_retries
            }
            
        except Exception as e:
            logger.error(f"Failed to get sync summary: {e}")
            return {
                'total_tasks': 0,
                'status_counts': {},
                'server_counts': {},
                'device_counts': {},
                'avg_retries': 0.0
            } 