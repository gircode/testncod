"""设备相关Schema"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, constr


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    mac_address: constr(regex=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    ip_address: Optional[str] = None
    group_id: Optional[int] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    ip_address: Optional[str] = None
    group_id: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(online|offline|error)$")


class DeviceResponse(DeviceBase):
    id: int
    status: str
    last_online: datetime

    class Config:
        from_attributes = True


class DeviceDetail(DeviceResponse):
    ports: List["PortResponse"] = []
    group: Optional["GroupResponse"] = None

    class Config:
        from_attributes = True
