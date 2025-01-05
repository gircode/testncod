"""VirtualHere服务管理模块"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

from ncod.utils.logger import logger
from ncod.utils.config import settings

SYSTEMD_SERVICE_TEMPLATE = """[Unit]
Description=VirtualHere USB Server
After=network.target

[Service]
Type=simple
User={user}
ExecStart={vh_binary} -c {config_file}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""


class VirtualHereService:
    """VirtualHere服务管理"""

    def __init__(self):
        self.config_path = settings.VH_CONFIG_PATH
        self.binary_path = self._get_binary_path()

    def _get_binary_path(self) -> Path:
        """获取VirtualHere二进制文件路径"""
        if sys.platform == "win32":
            return Path("C:/Program Files/VirtualHere/vhusbdwin64.exe")
        else:
            return Path("/usr/sbin/vhusbd")

    def install_service(self) -> bool:
        """安装系统服务"""
        try:
            if sys.platform == "win32":
                return self._install_windows_service()
            else:
                return self._install_linux_service()
        except Exception as e:
            logger.error(f"安装VirtualHere服务失败: {e}")
            return False

    def _install_windows_service(self) -> bool:
        """安装Windows服务"""
        try:
            # 使用sc.exe创建Windows服务
            cmd = [
                "sc.exe",
                "create",
                "VirtualHere",
                "binPath=",
                str(self.binary_path),
                "start=",
                "auto",
                "obj=",
                "LocalSystem",
            ]
            subprocess.run(cmd, check=True)

            # 设置服务描述
            cmd = ["sc.exe", "description", "VirtualHere", "VirtualHere USB Server"]
            subprocess.run(cmd, check=True)

            # 启动服务
            cmd = ["sc.exe", "start", "VirtualHere"]
            subprocess.run(cmd, check=True)

            logger.info("Windows VirtualHere服务安装成功")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"安装Windows VirtualHere服务失败: {e}")
            return False

    def _install_linux_service(self) -> bool:
        """安装Linux服务"""
        try:
            # 创建systemd服务文件
            service_content = SYSTEMD_SERVICE_TEMPLATE.format(
                user=os.getenv("USER", "root"),
                vh_binary=self.binary_path,
                config_file=self.config_path,
            )

            service_path = Path("/etc/systemd/system/virtualhere.service")
            service_path.write_text(service_content)

            # 重新加载systemd配置
            subprocess.run(["systemctl", "daemon-reload"], check=True)

            # 启用并启动服务
            subprocess.run(["systemctl", "enable", "virtualhere"], check=True)
            subprocess.run(["systemctl", "start", "virtualhere"], check=True)

            logger.info("Linux VirtualHere服务安装成功")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"安装Linux VirtualHere服务失败: {e}")
            return False

    def uninstall_service(self) -> bool:
        """卸载系统服务"""
        try:
            if sys.platform == "win32":
                return self._uninstall_windows_service()
            else:
                return self._uninstall_linux_service()
        except Exception as e:
            logger.error(f"卸载VirtualHere服务失败: {e}")
            return False

    def _uninstall_windows_service(self) -> bool:
        """卸载Windows服务"""
        try:
            # 停止服务
            subprocess.run(["sc.exe", "stop", "VirtualHere"], check=True)

            # 删除服务
            subprocess.run(["sc.exe", "delete", "VirtualHere"], check=True)

            logger.info("Windows VirtualHere服务卸载成功")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"卸载Windows VirtualHere服务失败: {e}")
            return False

    def _uninstall_linux_service(self) -> bool:
        """卸载Linux服务"""
        try:
            # 停止并禁用服务
            subprocess.run(["systemctl", "stop", "virtualhere"], check=True)
            subprocess.run(["systemctl", "disable", "virtualhere"], check=True)

            # 删除服务文件
            service_path = Path("/etc/systemd/system/virtualhere.service")
            if service_path.exists():
                service_path.unlink()

            # 重新加载systemd配置
            subprocess.run(["systemctl", "daemon-reload"], check=True)

            logger.info("Linux VirtualHere服务卸载成功")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"卸载Linux VirtualHere服务失败: {e}")
            return False

    def get_service_status(self) -> Optional[str]:
        """获取服务状态"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["sc.exe", "query", "VirtualHere"], capture_output=True, text=True
                )
                return result.stdout
            else:
                result = subprocess.run(
                    ["systemctl", "status", "virtualhere"],
                    capture_output=True,
                    text=True,
                )
                return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"获取VirtualHere服务状态失败: {e}")
            return None


# 创建全局服务实例
virtualhere_service = VirtualHereService()
