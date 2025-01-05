import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from ncod.master.models.user import User
from ncod.master.models.mac_address import MacAddress
from ncod.master.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class MacAuthManager:
    def __init__(self, config: Dict):
        self.config = config
        self.mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        self.max_macs_per_user = config.get("max_macs_per_user", 3)

    async def validate_mac_address(self, mac_address: str) -> bool:
        """验证MAC地址格式是否正确"""
        return bool(self.mac_pattern.match(mac_address))

    async def register_mac_address(self, user_id: int, mac_address: str) -> bool:
        """注册新的MAC地址"""
        try:
            # 验证MAC地址格式
            if not await self.validate_mac_address(mac_address):
                raise AuthenticationError("Invalid MAC address format")

            # 检查MAC地址是否已被注册
            existing_mac = await MacAddress.get_by_address(mac_address)
            if existing_mac:
                raise AuthenticationError("MAC address already registered")

            # 检查用户MAC地址数量限制
            user_macs = await MacAddress.get_by_user_id(user_id)
            if len(user_macs) >= self.max_macs_per_user:
                raise AuthenticationError(
                    "User has reached maximum number of MAC addresses (%d)"
                    % self.max_macs_per_user
                )

            # 注册新MAC地址
            new_mac = MacAddress(
                user_id=user_id,
                address=mac_address,
                registered_at=datetime.now(),
                last_used=datetime.now(),
                is_active=True,
            )
            await new_mac.save()

            logger.info("MAC address %s registered for user %d", mac_address, user_id)
            return True

        except Exception as e:
            logger.error("Error registering MAC address: %s", e)
            raise

    async def authenticate_mac(self, mac_address: str) -> Optional[int]:
        """验证MAC地址并返回关联的用户ID"""
        try:
            if not await self.validate_mac_address(mac_address):
                return None

            mac_record = await MacAddress.get_by_address(mac_address)
            if mac_record is None or not bool(mac_record.is_active):
                return None

            # 更新最后使用时间
            await mac_record.update(last_used=datetime.now())

            return int(mac_record.user_id)

        except Exception as e:
            logger.error("Error authenticating MAC address: %s", e)
            return None

    async def deactivate_mac(self, user_id: int, mac_address: str) -> bool:
        """停用MAC地址"""
        try:
            mac_record = await MacAddress.get_by_address(mac_address)
            if mac_record is None or int(mac_record.user_id) != user_id:
                return False

            # 修复属性赋值
            await mac_record.update(is_active=False)

            logger.info("MAC address %s deactivated for user %s", mac_address, user_id)
            return True

        except Exception as e:
            logger.error("Error deactivating MAC address: %s", e)
            return False

    async def get_user_macs(self, user_id: int) -> List[Dict]:
        """获取用户的所有MAC地址"""
        try:
            mac_records = await MacAddress.get_by_user_id(user_id)
            return [
                {
                    "address": mac.address,
                    "registered_at": mac.registered_at.isoformat(),
                    "last_used": mac.last_used.isoformat(),
                    "is_active": mac.is_active,
                }
                for mac in mac_records
            ]

        except Exception as e:
            logger.error("Error getting user MAC addresses: %s", e)
            return []

    async def check_mac_availability(self, mac_address: str) -> Tuple[bool, str]:
        """检查MAC地址是否可用"""
        try:
            if not await self.validate_mac_address(mac_address):
                return False, "Invalid MAC address format"

            existing_mac = await MacAddress.get_by_address(mac_address)
            if existing_mac:
                return False, "MAC address already registered"

            return True, "MAC address available"

        except Exception as e:
            logger.error("Error checking MAC address availability: %s", e)
            return False, str(e)

    async def cleanup_inactive_macs(self, days_threshold: int = 180) -> int:
        """清理长期未使用的MAC地址"""
        try:
            cleanup_date = datetime.now() - timedelta(days=days_threshold)
            count = await MacAddress.cleanup_inactive(cleanup_date)
            logger.info("Cleaned up %s inactive MAC addresses", count)
            return count

        except Exception as e:
            logger.error("Error cleaning up inactive MAC addresses: %s", e)
            return 0

    async def verify_mac_address(self, user: User, mac_address: str) -> bool:
        """验证MAC地址"""
        try:
            user_macs = await user.get_mac_addresses()
            return any(
                mac.address == mac_address and mac.is_active for mac in user_macs
            )
        except Exception as e:
            raise AuthenticationError(f"Error verifying MAC address: {str(e)}")

    async def authenticate_with_mac(
        self, username: str, mac_address: str
    ) -> Optional[User]:
        """使用MAC地址进行认证"""
        try:
            user = await User.get_by_username(username)
            if not user or user.status != "approved":
                return None

            if not await self.verify_mac_address(user, mac_address):
                return None

            return user

        except Exception as e:
            raise AuthenticationError(
                f"Error authenticating with MAC address: {str(e)}"
            )
