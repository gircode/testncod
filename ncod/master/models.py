from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MacAddress(db.Model):
    """MAC地址模型"""
    __tablename__ = 'mac_addresses'

    id = Column(Integer, primary_key=True)
    # 格式：XX:XX:XX:XX:XX:XX
    mac_address = Column(String(17), unique=True, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MacAddress {self.mac_address}>'


class Slave(db.Model):
    """从服务器模型"""
    __tablename__ = 'slaves'

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(15), nullable=False)  # IPv4地址
    mac_address = Column(String(17), nullable=False)  # MAC地址
    last_heartbeat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关联的设备
    devices = relationship('Device', back_populates='slave')

    def __repr__(self):
        return f'<Slave {self.hostname}>'


class Device(db.Model):
    """设备模型"""
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(String(255))
    status = Column(String(20), default='offline')
    vendor_id = Column(String(4))  # USB设备厂商ID
    product_id = Column(String(4))  # USB设备产品ID
    serial_number = Column(String(50))  # 设备序列号
    nickname = Column(String(100))  # 设备昵称
    last_seen = Column(DateTime)  # 最后一次在线时间
    slave_id = Column(Integer, ForeignKey('slaves.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关联的从服务器
    slave = relationship('Slave', back_populates='devices')
    # 关联的状态记录
    status_records = relationship('DeviceStatus', back_populates='device')
    # 关联的告警记录
    alerts = relationship('DeviceAlert', back_populates='device')
    # 关联的同步记录
    sync_records = relationship('DeviceSync', back_populates='device')

    def __repr__(self):
        return f'<Device {self.name}>'


class DeviceStatus(db.Model):
    """设备状态记录模型"""
    __tablename__ = 'device_status'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    status = Column(String(20), nullable=False)  # online/offline/in_use
    cpu_usage = Column(Float, default=0.0)  # CPU使用率
    memory_usage = Column(Float, default=0.0)  # 内存使用率
    disk_usage = Column(Float, default=0.0)  # 磁盘使用率
    network_usage = Column(Float, default=0.0)  # 网络使用率
    temperature = Column(Float)  # 温度
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联的设备
    device = relationship('Device', back_populates='status_records')

    def __repr__(self):
        return f'<DeviceStatus {self.device_id} {self.status}>'


class DeviceAlert(db.Model):
    """设备告警记录模型"""
    __tablename__ = 'device_alerts'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    type = Column(String(50), nullable=False)  # 告警类型
    severity = Column(String(20), nullable=False)  # critical/warning/info
    message = Column(String(255), nullable=False)  # 告警信息
    status = Column(String(20), default='active')  # active/resolved
    resolved_at = Column(DateTime)  # 解决时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关联的设备
    device = relationship('Device', back_populates='alerts')

    def __repr__(self):
        return f'<DeviceAlert {self.device_id} {self.type}>'


class DeviceSync(db.Model):
    """设备同步记录模型"""
    __tablename__ = 'device_syncs'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    status = Column(String(20), nullable=False)  # pending/completed/failed
    retry_count = Column(Integer, default=0)  # 重试次数
    error_message = Column(String(255))  # 错误信息
    completed_at = Column(DateTime)  # 完成时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关联的设备
    device = relationship('Device', back_populates='sync_records')

    def __repr__(self):
        return f'<DeviceSync {self.device_id} {self.status}>' 