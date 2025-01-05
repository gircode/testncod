import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class BackupManager:
    _instance: Optional['BackupManager'] = None
    _backup_dir: str = 'backups'
    
    def __new__(cls) -> 'BackupManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self) -> None:
        """确保备份目录存在"""
        try:
            os.makedirs(self._backup_dir, exist_ok=True)
            logger.debug(f"Backup directory ensured: {self._backup_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            raise
    
    def _get_backup_engine(self) -> Engine:
        """获取备份数据库引擎"""
        try:
            db_config = {
                'host': config.get('database.host'),
                'port': config.get('database.port'),
                'name': config.get('database.name'),
                'user': config.get('database.user'),
                'password': config.get('database.password')
            }
            
            url = (
                f"postgresql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}"
                f"/{db_config['name']}"
            )
            
            return create_engine(url)
            
        except Exception as e:
            logger.error(f"Failed to create backup engine: {e}")
            raise
    
    def create_backup(self, description: str = '') -> bool:
        """创建数据库备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(
                self._backup_dir,
                f"backup_{timestamp}.sql"
            )
            
            engine = self._get_backup_engine()
            connection = engine.raw_connection()
            
            try:
                cursor = connection.cursor()
                with open(backup_file, 'w', encoding='utf-8') as f:
                    cursor.copy_expert(
                        "COPY (SELECT * FROM pg_catalog.pg_dumpall) TO STDOUT",
                        f
                    )
                    
                # 创建备份描述文件
                if description:
                    desc_file = f"{backup_file}.desc"
                    with open(desc_file, 'w', encoding='utf-8') as f:
                        f.write(description)
                        
                logger.info(f"Database backup created: {backup_file}")
                return True
                
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_backup(self, backup_file: str) -> bool:
        """从备份文件恢复数据库"""
        try:
            if not os.path.exists(backup_file):
                logger.error(f"Backup file not found: {backup_file}")
                return False
                
            engine = self._get_backup_engine()
            connection = engine.raw_connection()
            
            try:
                cursor = connection.cursor()
                
                # 先删除现有数据库
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = current_database()"
                )
                cursor.execute("DROP DATABASE IF EXISTS current_database()")
                
                # 创建新数据库
                cursor.execute("CREATE DATABASE current_database()")
                
                # 恢复数据
                with open(backup_file, 'r', encoding='utf-8') as f:
                    cursor.copy_expert(
                        "COPY pg_catalog.pg_restore FROM STDIN",
                        f
                    )
                    
                connection.commit()
                logger.info(f"Database restored from: {backup_file}")
                return True
                
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份文件"""
        try:
            backups = []
            
            for file in os.listdir(self._backup_dir):
                if not file.endswith('.sql'):
                    continue
                    
                backup_file = os.path.join(self._backup_dir, file)
                desc_file = f"{backup_file}.desc"
                
                description = ''
                if os.path.exists(desc_file):
                    with open(desc_file, 'r', encoding='utf-8') as f:
                        description = f.read().strip()
                        
                stat = os.stat(backup_file)
                backups.append({
                    'file': file,
                    'path': backup_file,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime),
                    'description': description
                })
                
            return sorted(
                backups,
                key=lambda x: x['created_at'],
                reverse=True
            )
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_backup(self, backup_file: str) -> bool:
        """删除备份文件"""
        try:
            if not os.path.exists(backup_file):
                logger.error(f"Backup file not found: {backup_file}")
                return False
                
            os.remove(backup_file)
            
            desc_file = f"{backup_file}.desc"
            if os.path.exists(desc_file):
                os.remove(desc_file)
                
            logger.info(f"Backup deleted: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
    
    def clean_old_backups(self, days: int = 30) -> bool:
        """清理旧备份文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for backup in self.list_backups():
                if backup['created_at'] < cutoff_date:
                    self.delete_backup(backup['path'])
                    
            logger.info(f"Cleaned backups older than {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean old backups: {e}")
            return False
    
    def export_backup(
        self,
        backup_file: str,
        export_path: str
    ) -> bool:
        """导出备份文件"""
        try:
            if not os.path.exists(backup_file):
                logger.error(f"Backup file not found: {backup_file}")
                return False
                
            # 确保导出目录存在
            os.makedirs(
                os.path.dirname(export_path),
                exist_ok=True
            )
            
            # 复制备份文件
            shutil.copy2(backup_file, export_path)
            
            # 复制描述文件(如果存在)
            desc_file = f"{backup_file}.desc"
            if os.path.exists(desc_file):
                shutil.copy2(
                    desc_file,
                    f"{export_path}.desc"
                )
                
            logger.info(
                f"Backup exported: {backup_file} -> {export_path}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to export backup: {e}")
            return False
    
    def import_backup(
        self,
        import_path: str,
        description: str = ''
    ) -> bool:
        """导入备份文件"""
        try:
            if not os.path.exists(import_path):
                logger.error(f"Import file not found: {import_path}")
                return False
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(
                self._backup_dir,
                f"backup_{timestamp}.sql"
            )
            
            # 复制备份文件
            shutil.copy2(import_path, backup_file)
            
            # 创建描述文件
            if description:
                desc_file = f"{backup_file}.desc"
                with open(desc_file, 'w', encoding='utf-8') as f:
                    f.write(description)
                    
            logger.info(
                f"Backup imported: {import_path} -> {backup_file}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to import backup: {e}")
            return False 