from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ncod.core.db.database import get_db
from ncod.master.models.slave import Slave
from ncod.master.models.device import Device
from ncod.master.schemas.slave import SlaveRegister, SlaveReport

router = APIRouter(prefix="/api/v1/slaves", tags=["从服务器管理"])


@router.post("/register", response_model=dict)
async def register_slave(slave_data: SlaveRegister, db: Session = Depends(get_db)):
    """注册从服务器"""
    # 检查是否已存在
    existing_slave = (
        db.query(Slave).filter(Slave.mac_address == slave_data.mac_address).first()
    )

    if existing_slave:
        # 更新信息
        existing_slave.hostname = slave_data.hostname
        existing_slave.ip_address = slave_data.ip_address
        existing_slave.capabilities = slave_data.capabilities
        existing_slave.last_heartbeat = datetime.utcnow()
        slave_id = existing_slave.id
    else:
        # 创建新记录
        new_slave = Slave(**slave_data.dict())
        db.add(new_slave)
        db.commit()
        db.refresh(new_slave)
        slave_id = new_slave.id

    return {"slave_id": slave_id, "message": "Slave registered successfully"}


@router.post("/{slave_id}/report")
async def report_status(
    slave_id: int, report: SlaveReport, db: Session = Depends(get_db)
):
    """接收从服务器状态报告"""
    slave = db.query(Slave).filter(Slave.id == slave_id).first()
    if not slave:
        raise HTTPException(status_code=404, detail="Slave not found")

    # 更新从服务器状态
    slave.last_heartbeat = datetime.utcnow()

    # 更新设备状态
    for device_status in report.devices:
        device = db.query(Device).filter(Device.id == device_status.id).first()

        if device:
            device.status = device_status.status
            device.last_seen = datetime.utcnow()

    db.commit()

    return {"message": "Status report received"}
