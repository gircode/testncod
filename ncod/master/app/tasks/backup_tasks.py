"""
Backup tasks module
"""

import asyncio
from datetime import datetime
from pathlib import Path

from ..utils.backup import BackupManager


async def schedule_backups(backup_dir: str, source_dir: str, interval_hours: int = 24):
    """Schedule periodic backups of the source directory"""
    backup_manager = BackupManager(backup_dir)

    while True:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"scheduled_backup_{timestamp}"
            backup_manager.create_backup(source_dir, backup_name)

            # Clean up old backups (keep last 7 days)
            backups = backup_manager.list_backups()
            if len(backups) > 7:
                backups.sort()
                for old_backup in backups[:-7]:
                    backup_manager.delete_backup(old_backup)

        except Exception as e:
            print(f"Backup failed: {e}")

        await asyncio.sleep(interval_hours * 3600)
