#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from datetime import datetime
import logging
import gzip
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    def __init__(self, config):
        self.config = config
        self.backup_dir = config.get("backup_dir", "backups")
        self.db_name = config.get("db_name", "ncod")
        self.db_user = config.get("db_user", "postgres")
        self.db_host = config.get("db_host", "localhost")
        self.db_port = config.get("db_port", "5432")
        self.retention_days = config.get("retention_days", 7)

        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self):
        """创建数据库备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                self.backup_dir, f"{self.db_name}_{timestamp}.sql"
            )

            # 执行pg_dump
            cmd = [
                "pg_dump",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-F",
                "p",  # 纯文本格式
                "-f",
                backup_file,
                self.db_name,
            ]

            logger.info(f"Creating backup: {backup_file}")
            subprocess.run(cmd, check=True)

            # 压缩备份文件
            with open(backup_file, "rb") as f_in:
                with gzip.open(f"{backup_file}.gz", "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 删除未压缩的文件
            os.remove(backup_file)
            logger.info("Backup completed successfully")

            return f"{backup_file}.gz"

        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e}")
            raise

    def restore_backup(self, backup_file):
        """从备份文件恢复数据库"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Backup file not found: {backup_file}")

            # 如果是压缩文件，先解压
            if backup_file.endswith(".gz"):
                uncompressed_file = backup_file[:-3]
                with gzip.open(backup_file, "rb") as f_in:
                    with open(uncompressed_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_file = uncompressed_file

            # 执行恢复
            cmd = [
                "psql",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                self.db_name,
                "-f",
                backup_file,
            ]

            logger.info(f"Restoring from backup: {backup_file}")
            subprocess.run(cmd, check=True)

            # 清理解压的文件
            if backup_file.endswith(".sql"):
                os.remove(backup_file)

            logger.info("Restore completed successfully")

        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e}")
            raise

    def cleanup_old_backups(self):
        """清理过期的备份文件"""
        try:
            current_time = datetime.now()
            count = 0

            for filename in os.listdir(self.backup_dir):
                if not filename.endswith(".gz"):
                    continue

                filepath = os.path.join(self.backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                age_days = (current_time - file_time).days

                if age_days > self.retention_days:
                    os.remove(filepath)
                    count += 1
                    logger.info(f"Deleted old backup: {filename}")

            logger.info(f"Cleaned up {count} old backup files")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Database backup tool")
    parser.add_argument(
        "action", choices=["backup", "restore", "cleanup"], help="Action to perform"
    )
    parser.add_argument("--file", help="Backup file for restore")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    # 读取配置
    config = {
        "backup_dir": os.getenv("NCOD_BACKUP_DIR", "backups"),
        "db_name": os.getenv("NCOD_DB_NAME", "ncod"),
        "db_user": os.getenv("NCOD_DB_USER", "postgres"),
        "db_host": os.getenv("NCOD_DB_HOST", "localhost"),
        "db_port": os.getenv("NCOD_DB_PORT", "5432"),
        "retention_days": int(os.getenv("NCOD_BACKUP_RETENTION_DAYS", "7")),
    }

    backup = DatabaseBackup(config)

    try:
        if args.action == "backup":
            backup.create_backup()
        elif args.action == "restore":
            if not args.file:
                parser.error("--file is required for restore action")
            backup.restore_backup(args.file)
        elif args.action == "cleanup":
            backup.cleanup_old_backups()

    except Exception as e:
        logger.error(f"Error executing {args.action}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
