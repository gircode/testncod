"""USB设备Schema"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class USBPortBase(BaseModel):
    """USB端口基础Schema"""

    device_id: int
    port_number: int
    status: str = Field(..., description="空闲/占用/禁用")
    current_user_id: Optional[int] = None
    authorized_groups: List[int] = Field(default_factory=list)
    authorized_users: List[int] = Field(default_factory=list)


class PortQueueItem(BaseModel):
    """端口队列项"""

    user_id: int
    request_time: datetime
    estimated_duration: Optional[int] = None  # 预计使用时长(分钟)
