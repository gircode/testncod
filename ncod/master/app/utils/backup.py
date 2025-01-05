"""
Backup utility module
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:
    def __init__(self, backup_dir: str):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, source_dir: str, backup_name: str = None) -> str:
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory {source_dir} does not exist")

        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"

        backup_path = self.backup_dir / backup_name
        shutil.make_archive(str(backup_path), "zip", source_dir)
        return f"{backup_path}.zip"

    def restore_backup(self, backup_file: str, target_dir: str) -> None:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file {backup_file} does not exist")

        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        shutil.unpack_archive(backup_file, target_dir, "zip")

    def list_backups(self) -> list[str]:
        return [f.name for f in self.backup_dir.glob("*.zip")]

    def delete_backup(self, backup_name: str) -> bool:
        backup_path = self.backup_dir / backup_name
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
