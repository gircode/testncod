"""
Monitoring Logging Module
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class MonitoringLogFormatter(logging.Formatter):
    """Custom formatter for monitoring logs"""

    def __init__(self, include_timestamp: bool = True):
        """Initialize formatter"""
        self.include_timestamp = include_timestamp
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        # Create base log entry
        log_entry = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add timestamp if requested
        if self.include_timestamp:
            log_entry["timestamp"] = datetime.fromtimestamp(record.created).isoformat()

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_entry.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class MonitoringLogger:
    """Class for managing monitoring logs"""

    def __init__(
        self,
        name: str,
        log_dir: str,
        level: int = logging.INFO,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        include_timestamp: bool = True,
    ):
        """Initialize logger"""
        self.name = name
        self.log_dir = log_dir
        self.level = level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.include_timestamp = include_timestamp

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create formatter
        self.formatter = MonitoringLogFormatter(include_timestamp)

        # Create handlers
        self.handlers = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up log handlers"""
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)

        # Create handlers for different log levels
        levels = [
            ("error", logging.ERROR),
            ("warning", logging.WARNING),
            ("info", logging.INFO),
            ("debug", logging.DEBUG),
        ]

        for name, level in levels:
            if level >= self.level:
                handler = self._create_handler(name)
                handler.setLevel(level)
                handler.setFormatter(self.formatter)
                self.logger.addHandler(handler)
                self.handlers[name] = handler

    def _create_handler(self, level_name: str) -> logging.Handler:
        """Create a rotating file handler for the specified level"""
        log_file = os.path.join(self.log_dir, f"{self.name}_{level_name}.log")

        return logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )

    def log(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log a message with the specified level"""
        self.logger.log(
            level, message, extra={"extra": extra} if extra else None, exc_info=exc_info
        )

    def debug(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log a debug message"""
        self.log(logging.DEBUG, message, extra, exc_info)

    def info(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log an info message"""
        self.log(logging.INFO, message, extra, exc_info)

    def warning(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log a warning message"""
        self.log(logging.WARNING, message, extra, exc_info)

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log an error message"""
        self.log(logging.ERROR, message, extra, exc_info)

    def critical(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log a critical message"""
        self.log(logging.CRITICAL, message, extra, exc_info)

    def get_logs(
        self,
        level: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> list:
        """Get logs for the specified level and time range"""
        log_file = os.path.join(self.log_dir, f"{self.name}_{level}.log")

        if not os.path.exists(log_file):
            return []

        logs = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    log_entry = json.loads(line)

                    # Apply time filter if specified
                    if start_time or end_time:
                        log_time = datetime.fromisoformat(log_entry["timestamp"])

                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue

                    logs.append(log_entry)

                    # Apply limit if specified
                    if limit and len(logs) >= limit:
                        break

                except json.JSONDecodeError:
                    continue

        return logs

    def get_log_files(self) -> Dict[str, list]:
        """Get all log files including rotated ones"""
        log_files = {}

        for level in self.handlers.keys():
            pattern = f"{self.name}_{level}.log*"
            files = sorted(
                Path(self.log_dir).glob(pattern), key=os.path.getmtime, reverse=True
            )
            log_files[level] = [str(f) for f in files]

        return log_files

    def clear_logs(self, level: Optional[str] = None):
        """Clear logs for the specified level or all levels"""
        if level:
            if level in self.handlers:
                log_file = os.path.join(self.log_dir, f"{self.name}_{level}.log")
                self._clear_log_files(log_file)
        else:
            for level in self.handlers.keys():
                log_file = os.path.join(self.log_dir, f"{self.name}_{level}.log")
                self._clear_log_files(log_file)

    def _clear_log_files(self, base_file: str):
        """Clear all files for a log including rotated ones"""
        # Clear base log file
        if os.path.exists(base_file):
            os.truncate(base_file, 0)

        # Clear rotated files
        for i in range(1, self.backup_count + 1):
            rotated_file = f"{base_file}.{i}"
            if os.path.exists(rotated_file):
                os.remove(rotated_file)

    def close(self):
        """Close all handlers"""
        for handler in self.handlers.values():
            handler.close()
            self.logger.removeHandler(handler)
        self.handlers.clear()
