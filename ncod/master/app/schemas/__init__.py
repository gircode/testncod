"""Schema包"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .device import DeviceCreate, DeviceListResponse, DeviceResponse, DeviceUpdate
    from .slave import (
        ConnectionTestResponse,
        SlaveCreate,
        SlaveListResponse,
        SlaveResponse,
        SlaveUpdate,
    )
    from .user import UserCreate, UserResponse, UserUpdate

__all__ = [
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceListResponse",
    "SlaveCreate",
    "SlaveUpdate",
    "SlaveResponse",
    "SlaveListResponse",
    "ConnectionTestResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
]
