from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
from sqlalchemy.exc import SQLAlchemyError
from .models import Slave, MacAddress, Device
from .extensions import db, cache, logger


class SlaveManager:
    OFFLINE_TIMEOUT = 300  # 5分钟
    CACHE_TIMEOUT = 30    # 缓存超时时间（秒）
    
    def __init__(self):
        self.slaves = {}
        self._load_mac_addresses()
        
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def _load_mac_addresses(self) -> None:
        """
        从数据库加载已注册的MAC地址，使用缓存优化性能
        """
        try:
            addresses = MacAddress.query.filter_by(is_active=True).all()
            self.mac_addresses = {addr.mac_address for addr in addresses}
        except SQLAlchemyError as e:
            logger.error("Failed to load MAC addresses: %s", str(e))
            self.mac_addresses = set()
            
    def _clear_cache(self) -> None:
        """清除所有相关缓存"""
        cache.delete('slave_list')
        cache.delete_memoized(self._load_mac_addresses)
        
    def validate_client(self, client_type: str, mac_address: str = None) -> bool:
        """
        验证客户端
        :param client_type: 客户端类型 ('web' | 'client')
        :param mac_address: MAC地址（仅专用客户端需要）
        :return: bool
        """
        try:
            if client_type == 'web':
                return True
                
            if client_type == 'client':
                if not mac_address:
                    logger.warning("Client login attempt without MAC address")
                    return False
                    
                if not self._is_valid_mac_format(mac_address):
                    logger.warning("Invalid MAC address format: %s", mac_address)
                    return False
                    
                is_valid = mac_address in self.mac_addresses
                if not is_valid:
                    logger.warning("Unregistered MAC address: %s", mac_address)
                return is_valid
                
            logger.warning("Unknown client type: %s", client_type)
            return False
            
        except Exception as e:
            logger.error("Client validation error: %s", str(e))
            return False
            
    def _is_valid_mac_format(self, mac_address: str) -> bool:
        """
        验证MAC地址格式
        :param mac_address: MAC地址
        :return: bool
        """
        if not mac_address:
            return False
        pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        return bool(pattern.match(mac_address))

    def register_mac_address(self, mac_address: str, description: str = None) -> bool:
        """
        注册MAC地址
        :param mac_address: MAC地址
        :param description: 描述信息
        :return: bool
        """
        try:
            if not self._is_valid_mac_format(mac_address):
                msg = "Invalid MAC address format during registration: %s"
                logger.warning(msg, mac_address)
                return False

            # 检查是否已存在
            existing = MacAddress.query.filter_by(mac_address=mac_address).first()
            if existing:
                if existing.is_active:
                    logger.info("MAC address already registered: %s", mac_address)
                    return True
                # 重新激活
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
                if description:
                    existing.description = description
            else:
                # 创建新记录
                new_mac = MacAddress(
                    mac_address=mac_address,
                    description=description,
                    is_active=True
                )
                db.session.add(new_mac)

            db.session.commit()
            self.mac_addresses.add(mac_address)
            logger.info("Successfully registered MAC address: %s", mac_address)
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error("Failed to register MAC address %s: %s", mac_address, e)
            return False

    def unregister_mac_address(self, mac_address: str) -> bool:
        """
        注销MAC地址
        :param mac_address: MAC地址
        :return: bool
        """
        try:
            mac_record = MacAddress.query.filter_by(mac_address=mac_address).first()
            if not mac_record:
                logger.warning("MAC address not found: %s", mac_address)
                return False

            mac_record.is_active = False
            mac_record.updated_at = datetime.utcnow()
            db.session.commit()

            self.mac_addresses.discard(mac_address)
            logger.info("Successfully unregistered MAC address: %s", mac_address)
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error("Failed to unregister MAC address %s: %s", mac_address, e)
            return False

    def get_mac_addresses(self) -> List[Dict]:
        """
        获取所有已注册的MAC地址
        :return: List[Dict]
        """
        try:
            addresses = MacAddress.query.all()
            return [{
                'mac_address': addr.mac_address,
                'description': addr.description,
                'is_active': addr.is_active,
                'created_at': addr.created_at.isoformat(),
                'updated_at': addr.updated_at.isoformat() if addr.updated_at else None
            } for addr in addresses]
        except SQLAlchemyError as e:
            logger.error("Failed to get MAC addresses: %s", e)
            return []

    @staticmethod
    def get_all_slaves() -> List[Dict]:
        """获取所有从服务器列表"""
        try:
            # 尝试从缓存获取
            slaves = cache.get('slave_list')
            if slaves:
                return slaves
                
            # 从数据库获取
            slaves = []
            for slave in Slave.query.all():
                # 计算在线状态
                is_online = False
                if slave.last_heartbeat:
                    offline_threshold = (
                        datetime.utcnow().timestamp() - SlaveManager.OFFLINE_TIMEOUT
                    )
                    is_online = slave.last_heartbeat.timestamp() > offline_threshold

                slaves.append({
                    'id': slave.id,
                    'hostname': slave.hostname,
                    'ip_address': slave.ip_address,
                    'mac_address': slave.mac_address,
                    'status': 'online' if is_online else 'offline',
                    'last_heartbeat': (
                        slave.last_heartbeat.isoformat()
                        if slave.last_heartbeat else None
                    ),
                    'created_at': slave.created_at.isoformat()
                })
                
            # 更新缓存
            cache.set('slave_list', slaves, timeout=30)
            return slaves
            
        except (SQLAlchemyError, ValueError) as e:
            logger.error("Failed to get slave list: %s", e)
            return []
    
    @staticmethod
    def get_slave(slave_id: int) -> Optional[Dict]:
        """获取单个从服务器信息"""
        try:
            slave = Slave.query.get(slave_id)
            if not slave:
                return None
                
            # 计算在线状态
            is_online = False
            if slave.last_heartbeat:
                offline_threshold = (
                    datetime.utcnow().timestamp() - SlaveManager.OFFLINE_TIMEOUT
                )
                is_online = slave.last_heartbeat.timestamp() > offline_threshold

            return {
                'id': slave.id,
                'hostname': slave.hostname,
                'ip_address': slave.ip_address,
                'mac_address': slave.mac_address,
                'status': 'online' if is_online else 'offline',
                'last_heartbeat': (
                    slave.last_heartbeat.isoformat()
                    if slave.last_heartbeat else None
                ),
                'created_at': slave.created_at.isoformat()
            }
            
        except (SQLAlchemyError, ValueError) as e:
            logger.error("Failed to get slave %s: %s", slave_id, e)
            return None
    
    @staticmethod
    def register_slave(
        hostname: str,
        ip_address: str,
        mac_address: str
    ) -> Optional[Dict]:
        """
        注册从服务器
        :param hostname: 主机名
        :param ip_address: IP地址
        :param mac_address: MAC地址
        :return: Optional[Dict] 包含注册结果的字典
        """
        try:
            with db.session.begin_nested():
                existing_slave = Slave.query.filter_by(
                    mac_address=mac_address
                ).first()
                
                if existing_slave:
                    existing_slave.hostname = hostname
                    existing_slave.ip_address = ip_address
                    existing_slave.status = 'online'
                    existing_slave.last_heartbeat = datetime.utcnow()
                    result = {
                        'id': existing_slave.id,
                        'status': 'updated'
                    }
                else:
                    new_slave = Slave(
                        hostname=hostname,
                        ip_address=ip_address,
                        mac_address=mac_address,
                        status='online',
                        last_heartbeat=datetime.utcnow()
                    )
                    db.session.add(new_slave)
                    db.session.flush()
                    result = {
                        'id': new_slave.id,
                        'status': 'created'
                    }
                    
            db.session.commit()
            cache.delete('slave_list')
            return result
            
        except SQLAlchemyError as e:
            logger.error("Failed to register slave: %s", str(e))
            db.session.rollback()
            return None
        except Exception as e:
            logger.error("Unexpected error during slave registration: %s", str(e))
            db.session.rollback()
            return None
            
    @staticmethod
    def update_slave_status(slave_id: int, status: str) -> bool:
        """更新从服务器状态"""
        try:
            slave = Slave.query.get(slave_id)
            if not slave:
                return False
                
            slave.status = status
            slave.last_heartbeat = datetime.utcnow()
            db.session.commit()
            
            # 清除缓存
            cache.delete('slave_list')
            return True
            
        except Exception as e:
            logger.error(f"Failed to update slave status {slave_id}: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def check_offline_slaves() -> List[int]:
        """
        检查离线的从服务器，使用批量更新优化性能
        :return: List[int] 离线从服务器ID列表
        """
        try:
            offline_threshold = datetime.utcnow() - timedelta(
                seconds=SlaveManager.OFFLINE_TIMEOUT
            )
            
            # 使用批量更新提高性能
            offline_query = (
                Slave.query
                .filter(Slave.status == 'online')
                .filter(
                    (Slave.last_heartbeat == None) |  # noqa
                    (Slave.last_heartbeat < offline_threshold)
                )
            )
            
            # 获取离线从服务器ID
            offline_ids = [slave.id for slave in offline_query.all()]
            
            if offline_ids:
                # 批量更新状态
                offline_query.update(
                    {'status': 'offline'},
                    synchronize_session=False
                )
                db.session.commit()
                cache.delete('slave_list')
                
            return offline_ids
            
        except SQLAlchemyError as e:
            logger.error("Database error during offline check: %s", str(e))
            db.session.rollback()
            return []
        except Exception as e:
            logger.error("Unexpected error during offline check: %s", str(e))
            db.session.rollback()
            return []
    
    @staticmethod
    def get_slave_devices(slave_id: int) -> List[Dict]:
        """获取从服务器的设备列表"""
        try:
            devices = []
            for device in Device.query.filter_by(slave_id=slave_id):
                devices.append({
                    'id': device.id,
                    'vendor_id': device.vendor_id,
                    'product_id': device.product_id,
                    'serial_number': device.serial_number,
                    'nickname': device.nickname,
                    'status': device.status,
                    'last_seen': (
                        device.last_seen.isoformat()
                        if device.last_seen else None
                    ),
                    'created_at': device.created_at.isoformat()
                })
                
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get slave devices {slave_id}: {e}")
            return []
    
    @staticmethod
    def delete_slave(slave_id: int) -> bool:
        """删除从服务器"""
        try:
            slave = Slave.query.get(slave_id)
            if not slave:
                return False
                
            # 删除从服务器及其关联的设备
            db.session.delete(slave)
            db.session.commit()
            
            # 清除缓存
            cache.delete('slave_list')
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete slave {slave_id}: {e}")
            db.session.rollback()
            return False 