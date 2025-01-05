import os
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Optional
from ..config import Config

logger = logging.getLogger(__name__)

def create_backup() -> Optional[str]:
    """创建数据库备份"""
    try:
        # 创建备份目录
        os.makedirs(Config.BACKUP_PATH, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(Config.BACKUP_PATH, f'backup_{timestamp}.sql')
        
        # 从数据库URI中提取信息
        db_url = Config.SQLALCHEMY_DATABASE_URI
        db_name = db_url.split('/')[-1]
        db_user = db_url.split('://')[1].split(':')[0]
        db_pass = db_url.split(':')[2].split('@')[0]
        db_host = db_url.split('@')[1].split(':')[0]
        
        # 执行pg_dump命令
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-U', db_user,
            '-F', 'c',
            '-b',
            '-v',
            '-f', backup_file,
            db_name
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_pass
        
        subprocess.run(cmd, env=env, check=True)
        logger.info(f"Database backup created: {backup_file}")
        
        return backup_file
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return None

def restore_backup(backup_file: str) -> bool:
    """从备份文件恢复数据库"""
    try:
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False
            
        # 从数据库URI中提取信息
        db_url = Config.SQLALCHEMY_DATABASE_URI
        db_name = db_url.split('/')[-1]
        db_user = db_url.split('://')[1].split(':')[0]
        db_pass = db_url.split(':')[2].split('@')[0]
        db_host = db_url.split('@')[1].split(':')[0]
        
        # 执行pg_restore命令
        cmd = [
            'pg_restore',
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-v',
            backup_file
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_pass
        
        subprocess.run(cmd, env=env, check=True)
        logger.info(f"Database restored from: {backup_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False

def cleanup_old_backups() -> None:
    """清理过期的备份文件"""
    try:
        if not os.path.exists(Config.BACKUP_PATH):
            return
            
        # 计算过期时间
        expiry_date = datetime.now() - timedelta(days=Config.BACKUP_KEEP_DAYS)
        
        # 遍历备份目录
        for filename in os.listdir(Config.BACKUP_PATH):
            if not filename.startswith('backup_'):
                continue
                
            filepath = os.path.join(Config.BACKUP_PATH, filename)
            file_date = datetime.strptime(filename.split('_')[1].split('.')[0], '%Y%m%d')
            
            if file_date < expiry_date:
                os.remove(filepath)
                logger.info(f"Removed old backup: {filepath}")
                
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")

def init_backup_schedule(app) -> None:
    """初始化备份计划"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # 每天凌晨3点执行备份
        scheduler.add_job(create_backup, 'cron', hour=3)
        
        # 每周日凌晨4点清理过期备份
        scheduler.add_job(cleanup_old_backups, 'cron', day_of_week='sun', hour=4)
        
        scheduler.start()
        logger.info("Backup schedule initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize backup schedule: {e}") 