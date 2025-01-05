"""VirtualHere客户端"""

import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from ncod.core.logger import device_logger as logger
from ncod.core.config import config


class VirtualHereClient:
    def __init__(self):
        self.vhclient_path = config.virtualhere_config["client_path"]
        self.server_port = config.virtualhere_config["server_port"]
        self.process: Optional[asyncio.subprocess.Process] = None

    async def initialize(self):
        """初始化VirtualHere客户端"""
        try:
            # 启动VirtualHere客户端进程
            self.process = await asyncio.create_subprocess_exec(
                self.vhclient_path,
                "--port",
                str(self.server_port),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            logger.info("VirtualHere client started successfully")
        except Exception as e:
            logger.error(f"Failed to start VirtualHere client: {e}")
            raise

    async def cleanup(self):
        """清理资源"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None

    async def get_devices(self) -> List[Dict[str, Any]]:
        """获取设备列表"""
        try:
            result = await self._execute_command("list")
            return self._parse_device_list(result)
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            return []

    async def connect_device(self, device_id: str) -> bool:
        """连接设备"""
        try:
            await self._execute_command(f"use {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect device {device_id}: {e}")
            return False

    async def disconnect_device(self, device_id: str) -> bool:
        """断开设备"""
        try:
            await self._execute_command(f"stop {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect device {device_id}: {e}")
            return False

    async def _execute_command(self, command: str) -> str:
        """执行VirtualHere命令"""
        process = await asyncio.create_subprocess_exec(
            self.vhclient_path,
            "--cmd",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Command failed: {stderr.decode()}")
        return stdout.decode()

    def _parse_device_list(self, output: str) -> List[Dict[str, Any]]:
        """解析设备列表输出"""
        devices = []
        current_device = {}

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("Device "):
                if current_device:
                    devices.append(current_device)
                current_device = {"id": line.split()[1]}
            elif ":" in line:
                key, value = line.split(":", 1)
                current_device[key.strip().lower()] = value.strip()

        if current_device:
            devices.append(current_device)

        return devices
