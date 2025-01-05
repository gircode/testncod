import logging
from typing import Dict, List
from virtualhere import VirtualHereClient

logger = logging.getLogger(__name__)

class DeviceMonitor:
    def __init__(self):
        self.vh_client = VirtualHereClient()
        
    def get_device_status(self) -> List[Dict]:
        """获取所有设备状态"""
        try:
            return self.vh_client.get_device_list()
        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            return []
            
    def check_device_availability(self, device_id: str) -> bool:
        """检查设备是否可用"""
        try:
            devices = self.vh_client.get_device_list()
            for device in devices:
                if f"{device['vendor_id']}.{device['product_id']}" == device_id:
                    return device['status'] == 'available'
            return False
        except Exception as e:
            logger.error(f"Failed to check device availability: {e}")
            return False
            
    def get_device_info(self, device_id: str) -> Dict:
        """获取设备详细信息"""
        try:
            info = self.vh_client.execute_command(f'DEVICE INFO,{device_id}')
            return self._parse_device_info(info)
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return {}
            
    def _parse_device_info(self, info: str) -> Dict:
        """解析设备信息"""
        result = {}
        try:
            for line in info.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip()
            return result
        except Exception as e:
            logger.error(f"Failed to parse device info: {e}")
            return {} 