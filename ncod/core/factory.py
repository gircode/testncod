"""服务工厂"""

from typing import Dict, Type, Any
from ncod.core.services import system_monitor, device_service, security_service


class ServiceFactory:
    _services: Dict[str, Any] = {
        "monitor": system_monitor,
        "device": device_service,
        "security": security_service,
    }

    @classmethod
    def get_service(cls, service_name: str) -> Any:
        """获取服务实例"""
        if service_name not in cls._services:
            raise ValueError(f"未知的服务: {service_name}")
        return cls._services[service_name]

    @classmethod
    def register_service(cls, name: str, service: Any) -> None:
        """注册新服务"""
        cls._services[name] = service
