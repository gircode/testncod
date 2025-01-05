"""
审计日志数据模式
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    """审计日志基础模式"""

    action: str = Field(..., description="操作类型")
    status: str = Field(..., description="操作状态")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    resource_type: Optional[str] = Field(None, description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    error_message: Optional[str] = Field(None, description="错误信息")


class AuditLogResponse(AuditLogBase):
    """审计日志响应模式"""

    id: int = Field(..., description="日志ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应模式"""

    items: List[AuditLogResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    pages: int = Field(..., description="总页数")


class UserActivityResponse(BaseModel):
    """用户活动统计响应模式"""

    total_actions: int = Field(..., description="总操作数")
    success_rate: float = Field(..., description="成功率")
    action_distribution: Dict[str, int] = Field(..., description="操作类型分布")
    resource_distribution: Dict[str, int] = Field(..., description="资源类型分布")
    daily_activity: Dict[str, int] = Field(..., description="每日活动数")
    error_count: int = Field(..., description="错误数")


class DailyMetrics(BaseModel):
    """每日指标模式"""

    total_events: int = Field(..., description="总事件数")
    successful_events: int = Field(..., description="成功事件数")
    failed_events: int = Field(..., description="失败事件数")
    suspicious_events: int = Field(..., description="可疑事件数")


class SecurityMetricsResponse(BaseModel):
    """安全指标响应模式"""

    login_success_rate: float = Field(..., description="登录成功率")
    failed_login_attempts: int = Field(..., description="失败登录尝试次数")
    password_changes: int = Field(..., description="密码修改次数")
    two_factor_adoption_rate: float = Field(..., description="双因素认证采用率")
    suspicious_activities: int = Field(..., description="可疑活动数")
    daily_metrics: Dict[str, DailyMetrics] = Field(..., description="每日指标")
