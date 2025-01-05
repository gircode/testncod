"""设备批量操作服务"""

from typing import List, Dict
from ncod.core.logger import LoggerManager
from ncod.master.services.device import DeviceService
from ncod.master.models.device import Device

logger = LoggerManager.get_logger(__name__)


class DeviceBatchService:
    """设备批量操作服务"""

    def __init__(self):
        self.device_service = DeviceService()

    async def batch_update_status(self, device_ids: List[str], status: str) -> Dict:
        """批量更新设备状态"""
        try:
            success = []
            failed = []
            for device_id in device_ids:
                try:
                    result = await self.device_service.update_device(
                        device_id, {"status": status}
                    )
                    if result[0]:  # 成功
                        success.append(device_id)
                    else:
                        logger.error(
                            f"Failed to update device {device_id}: {result[1]}"
                        )
                        failed.append(device_id)
                except Exception as e:
                    logger.error(f"Failed to update device {device_id}: {e}")
                    failed.append(device_id)

            return {
                "success": success,
                "failed": failed,
                "total": len(device_ids),
                "success_count": len(success),
                "failed_count": len(failed),
            }
        except Exception as e:
            logger.error(f"Batch update status failed: {e}")
            raise

    async def batch_assign_organization(
        self, device_ids: List[str], organization_id: str
    ) -> Dict:
        """批量分配组织"""
        try:
            success = []
            failed = []
            for device_id in device_ids:
                try:
                    result = await self.device_service.update_device(
                        device_id, {"organization_id": organization_id}
                    )
                    if result[0]:  # 成功
                        success.append(device_id)
                    else:
                        logger.error(
                            f"Failed to assign device {device_id}: {result[1]}"
                        )
                        failed.append(device_id)
                except Exception as e:
                    logger.error(f"Failed to assign device {device_id}: {e}")
                    failed.append(device_id)

            return {
                "success": success,
                "failed": failed,
                "total": len(device_ids),
                "success_count": len(success),
                "failed_count": len(failed),
            }
        except Exception as e:
            logger.error(f"Batch assign organization failed: {e}")
            raise

    async def batch_delete(self, device_ids: List[str]) -> Dict:
        """批量删除设备"""
        try:
            success = []
            failed = []
            for device_id in device_ids:
                try:
                    result = await self.device_service.delete_device(device_id)
                    if result[0]:  # 成功
                        success.append(device_id)
                    else:
                        logger.error(
                            f"Failed to delete device {device_id}: {result[1]}"
                        )
                        failed.append(device_id)
                except Exception as e:
                    logger.error(f"Failed to delete device {device_id}: {e}")
                    failed.append(device_id)

            return {
                "success": success,
                "failed": failed,
                "total": len(device_ids),
                "success_count": len(success),
                "failed_count": len(failed),
            }
        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            raise


def create_device_batch_service() -> DeviceBatchService:
    """创建设备批量操作服务实例"""
    return DeviceBatchService()
