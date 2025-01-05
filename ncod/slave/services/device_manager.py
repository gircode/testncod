"""从服务器设备管理器"""

import asyncio
import json
from typing import Dict, Optional, List
import aiohttp
from fastapi import WebSocket
from pathlib import Path
import logging

from ncod.core.config import settings
from ncod.utils.logger import logger
from ncod.utils.usb_utils import usb_controller


class DeviceManager:
    """USB设备管理器"""

    def __init__(self):
        self.config_path = Path(settings.VIRTUALHERE_CONFIG_PATH)
        self.event_scripts_path = Path(settings.EVENT_SCRIPTS_PATH)
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """设置VirtualHere事件处理器"""
        event_scripts = {
            "onBind": self._create_bind_script,
            "onUnbind": self._create_unbind_script,
            "onEnumeration": self._create_enumeration_script,
            "onDeviceUnplug": self._create_unplug_script,
        }

        for event, creator in event_scripts.items():
            script_path = self.event_scripts_path / f"{event}.sh"
            if not script_path.exists():
                creator(script_path)
                script_path.chmod(0o755)

    def _create_bind_script(self, path: Path):
        """创建设备绑定事件处理脚本"""
        script_content = """#!/bin/bash
logger -t virtualhere "Device bound: $VENDOR_ID.$PRODUCT_ID ($SERIAL) by $CLIENT_IP"
# 通知主服务器设备已绑定
curl -X POST http://${MASTER_HOST}:${MASTER_PORT}/api/v1/devices/bound \\
    -H "Content-Type: application/json" \\
    -d "{
        'vendor_id': '$VENDOR_ID',
        'product_id': '$PRODUCT_ID',
        'serial': '$SERIAL',
        'client_ip': '$CLIENT_IP'
    }"
"""
        path.write_text(script_content)

    def _create_unbind_script(self, path: Path):
        """创建设备解绑事件处理脚本"""
        script_content = """#!/bin/bash
logger -t virtualhere "Device unbound: $VENDOR_ID.$PRODUCT_ID ($SERIAL)"
"""
        path.write_text(script_content)

    def _create_enumeration_script(self, path: Path):
        """创建设备枚举事件处理脚本"""
        script_content = """#!/bin/bash
logger -t virtualhere "Device enumerated: $VENDOR_ID.$PRODUCT_ID ($SERIAL)"
"""
        path.write_text(script_content)

    def _create_unplug_script(self, path: Path):
        """创建设备拔出事件处理脚本"""
        script_content = """#!/bin/bash
logger -t virtualhere "Device unplugged: $VENDOR_ID.$PRODUCT_ID ($SERIAL)"
"""
        path.write_text(script_content)
