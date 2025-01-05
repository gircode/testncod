"""设备服务"""

from typing import Dict, List, Optional, Tuple
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.device import Device
from ncod.master.models.organization import Organization
from ncod.master.models.slave import Slave

logger = setup_logger("device_service")


class DeviceService:
    """设备服务"""

    def __init__(self):
        self.transaction = transaction_manager

    async def create_device(self, data: Dict) -> Tuple[bool, str, Optional[Device]]:
        """创建设备"""
        try:
            async with self.transaction.transaction() as session:
                # 检查MAC地址是否存在
                if await Device.get_by_mac(session, data["mac_address"]):
                    return False, "Device MAC address already exists", None

                # 检查组织是否存在
                if "organization_id" in data:
                    org = await session.get(Organization, data["organization_id"])
                    if not org:
                        return False, "Organization not found", None

                # 检查从服务器是否存在
                if "slave_id" in data:
                    slave = await session.get(Slave, data["slave_id"])
                    if not slave:
                        return False, "Slave server not found", None

                # 创建设备
                device = Device(
                    name=data["name"],
                    mac_address=data["mac_address"],
                    ip_address=data.get("ip_address"),
                    description=data.get("description"),
                    is_active=data.get("is_active", True),
                    organization_id=data.get("organization_id"),
                    slave_id=data.get("slave_id"),
                )

                session.add(device)
                await session.commit()
                await session.refresh(device)

                return True, "Device created successfully", device
        except Exception as e:
            logger.error(f"Error creating device: {e}")
            return False, str(e), None

    async def update_device(
        self, device_id: str, data: Dict
    ) -> Tuple[bool, str, Optional[Device]]:
        """更新设备"""
        try:
            async with self.transaction.transaction() as session:
                device = await session.get(Device, device_id)
                if not device:
                    return False, "Device not found", None

                # 检查MAC地址是否重复
                if "mac_address" in data:
                    existing = await Device.get_by_mac(session, data["mac_address"])
                    if existing and existing.id != device_id:
                        return False, "Device MAC address already exists", None
                    device.mac_address = data["mac_address"]

                # 更新基本信息
                if "name" in data:
                    device.name = data["name"]
                if "ip_address" in data:
                    device.ip_address = data["ip_address"]
                if "description" in data:
                    device.description = data["description"]
                if "is_active" in data:
                    device.is_active = data["is_active"]

                # 更新关联
                if "organization_id" in data:
                    if data["organization_id"]:
                        org = await session.get(Organization, data["organization_id"])
                        if not org:
                            return False, "Organization not found", None
                    device.organization_id = data["organization_id"]

                if "slave_id" in data:
                    if data["slave_id"]:
                        slave = await session.get(Slave, data["slave_id"])
                        if not slave:
                            return False, "Slave server not found", None
                    device.slave_id = data["slave_id"]

                await session.commit()
                await session.refresh(device)

                return True, "Device updated successfully", device
        except Exception as e:
            logger.error(f"Error updating device: {e}")
            return False, str(e), None

    async def delete_device(self, device_id: str) -> Tuple[bool, str]:
        """删除设备"""
        try:
            async with self.transaction.transaction() as session:
                device = await session.get(Device, device_id)
                if not device:
                    return False, "Device not found"

                await session.delete(device)
                await session.commit()

                return True, "Device deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting device: {e}")
            return False, str(e)

    async def get_device(self, device_id: str) -> Optional[Dict]:
        """获取设备"""
        try:
            async with self.transaction.transaction() as session:
                device = await session.get(Device, device_id)
                return device.to_dict() if device else None
        except Exception as e:
            logger.error(f"Error getting device: {e}")
            return None

    async def list_devices(
        self, organization_id: Optional[str] = None, slave_id: Optional[str] = None
    ) -> List[Dict]:
        """获取设备列表"""
        try:
            async with self.transaction.transaction() as session:
                if organization_id:
                    devices = await Device.get_by_organization(session, organization_id)
                elif slave_id:
                    devices = await Device.get_by_slave(session, slave_id)
                else:
                    stmt = select(Device)
                    result = await session.execute(stmt)
                    devices = result.scalars().all()

                return [device.to_dict() for device in devices]
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return []


# 创建全局设备服务实例
device_service = DeviceService()
