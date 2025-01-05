import re
import subprocess
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_mac_address() -> Optional[str]:
    """获取系统MAC地址"""
    try:
        if platform.system() == "Windows":
            # Windows系统使用ipconfig命令
            output = subprocess.check_output("ipconfig /all").decode()
            mac_addresses = re.findall(r"物理地址.+?([0-9A-F]{2}(-[0-9A-F]{2}){5})", output)
            if mac_addresses:
                return mac_addresses[0][0]
        else:
            # Linux/Unix系统使用ifconfig命令
            output = subprocess.check_output(["ifconfig"]).decode()
            mac_addresses = re.findall(r"ether\s+([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})", output)
            if mac_addresses:
                return mac_addresses[0]
        return None
    except Exception as e:
        logger.error(f"Failed to get MAC address: {e}")
        return None

def validate_mac() -> Optional[str]:
    """验证MAC地址"""
    mac_address = get_mac_address()
    if not mac_address:
        logger.error("Could not find MAC address")
        return None
        
    # 统一MAC地址格式为xx:xx:xx:xx:xx:xx
    mac_address = mac_address.replace("-", ":")
    
    # 验证MAC地址格式
    if not re.match(r"^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$", mac_address):
        logger.error(f"Invalid MAC address format: {mac_address}")
        return None
        
    return mac_address.lower()

def is_valid_mac(mac_address: str) -> bool:
    """检查MAC地址是否有效"""
    if not mac_address:
        return False
        
    # 统一MAC地址格式为xx:xx:xx:xx:xx:xx
    mac_address = mac_address.replace("-", ":")
    
    # 验证MAC地址格式
    if not re.match(r"^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$", mac_address):
        return False
        
    # 检查是否为全0地址
    if mac_address == "00:00:00:00:00:00":
        return False
        
    # 检查是否为广播地址
    if mac_address == "ff:ff:ff:ff:ff:ff":
        return False
        
    return True 