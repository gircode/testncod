"""
设备控制模块
"""

import asyncio
import json
import socket
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import aiohttp
except ImportError:
    import pip

    pip.main(["install", "aiohttp"])
    import aiohttp

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    import pip

    pip.main(["install", "pyserial"])
    import serial
    import serial.tools.list_ports

try:
    import modbus_tk
    import modbus_tk.defines as cst
    from modbus_tk import modbus_rtu, modbus_tcp
except ImportError:
    import pip

    pip.main(["install", "modbus_tk"])
    import modbus_tk
    import modbus_tk.defines as cst
    from modbus_tk import modbus_rtu, modbus_tcp


class DeviceType(Enum):
    """设备类型"""

    HTTP = "http"
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    SOCKET = "socket"
    SERIAL = "serial"


class DeviceStatus(Enum):
    """设备状态"""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class DeviceConfig:
    """设备配置"""

    device_id: str
    name: str
    type: DeviceType
    host: Optional[str] = None
    port: Optional[int] = None
    timeout: int = 30
    retry_count: int = 3
    retry_interval: int = 5

    # HTTP设备配置
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    # Modbus设备配置
    slave_id: Optional[int] = None
    registers: Optional[List[Dict[str, Any]]] = None

    # 串口设备配置
    com_port: Optional[str] = None
    baudrate: Optional[int] = None
    bytesize: Optional[int] = None
    parity: Optional[str] = None
    stopbits: Optional[int] = None


@dataclass
class DeviceCommand:
    """设备命令"""

    command: str
    params: Dict[str, Any]
    timeout: Optional[int] = None


@dataclass
class CommandResult:
    """命令执行结果"""

    success: bool
    message: str
    data: Any = None
    error: Optional[Exception] = None


class DeviceConnection:
    """设备连接基类"""

    def __init__(self, config: DeviceConfig):
        self.config = config
        self.connected = False
        self.last_error = None

    async def connect(self) -> bool:
        """连接设备"""
        raise NotImplementedError

    async def disconnect(self):
        """断开连接"""
        raise NotImplementedError

    async def send_command(self, command: DeviceCommand) -> CommandResult:
        """发送命令"""
        raise NotImplementedError

    async def read_data(self) -> Any:
        """读取数据"""
        raise NotImplementedError


class HttpDeviceConnection(DeviceConnection):
    """HTTP设备连接"""

    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """连接设备"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    base_url=self.config.base_url,
                    headers=self.config.headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                )
            self.connected = True
            return True
        except Exception as e:
            self.last_error = e
            return False

    async def disconnect(self):
        """断开连接"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False

    async def send_command(self, command: DeviceCommand) -> CommandResult:
        """发送命令"""
        if not self.connected or not self.session:
            return CommandResult(
                success=False, message="设备未连接", error=Exception("设备未连接")
            )

        try:
            timeout = command.timeout or self.config.timeout
            async with self.session.request(
                method=command.command,
                url=command.params.get("url", ""),
                json=command.params.get("data"),
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                return CommandResult(
                    success=True, message="命令执行成功", data=await response.json()
                )
        except Exception as e:
            self.last_error = e
            return CommandResult(
                success=False, message=f"命令执行失败: {str(e)}", error=e
            )

    async def read_data(self) -> Any:
        """读取数据"""
        if not self.connected or not self.session:
            raise Exception("设备未连接")

        try:
            async with self.session.get("") as response:
                return await response.json()
        except Exception as e:
            self.last_error = e
            raise


class ModbusTcpDeviceConnection(DeviceConnection):
    """Modbus TCP设备连接"""

    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.master = None
        self.slave = None

    async def connect(self) -> bool:
        """连接设备"""
        try:
            self.master = modbus_tcp.TcpMaster(
                host=self.config.host,
                port=self.config.port,
                timeout_in_sec=self.config.timeout,
            )
            self.slave = self.master.get_slave(self.config.slave_id or 1)
            self.connected = True
            return True
        except Exception as e:
            self.last_error = e
            return False

    async def disconnect(self):
        """断开连接"""
        if self.master:
            self.master.close()
            self.master = None
            self.slave = None
        self.connected = False

    async def send_command(self, command: DeviceCommand) -> CommandResult:
        """发送命令"""
        if not self.connected or not self.slave:
            return CommandResult(
                success=False, message="设备未连接", error=Exception("设备未连接")
            )

        try:
            func_code = getattr(cst, command.command, None)
            if not func_code:
                raise ValueError(f"无效的功能码: {command.command}")

            address = command.params.get("address", 0)
            data = command.params.get("data", [])

            if func_code == cst.READ_COILS:
                result = await self.slave.execute(
                    func_code, address, data[0] if data else 1
                )
            elif func_code == cst.READ_DISCRETE_INPUTS:
                result = await self.slave.execute(
                    func_code, address, data[0] if data else 1
                )
            elif func_code == cst.READ_HOLDING_REGISTERS:
                result = await self.slave.execute(
                    func_code, address, data[0] if data else 1
                )
            elif func_code == cst.READ_INPUT_REGISTERS:
                result = await self.slave.execute(
                    func_code, address, data[0] if data else 1
                )
            elif func_code == cst.WRITE_SINGLE_COIL:
                result = await self.slave.execute(
                    func_code, address, output_value=data[0]
                )
            elif func_code == cst.WRITE_SINGLE_REGISTER:
                result = await self.slave.execute(
                    func_code, address, output_value=data[0]
                )
            elif func_code == cst.WRITE_MULTIPLE_COILS:
                result = await self.slave.execute(func_code, address, output_value=data)
            elif func_code == cst.WRITE_MULTIPLE_REGISTERS:
                result = await self.slave.execute(func_code, address, output_value=data)
            else:
                raise ValueError(f"不支持的功能码: {command.command}")

            return CommandResult(success=True, message="命令执行成功", data=result)
        except Exception as e:
            self.last_error = e
            return CommandResult(
                success=False, message=f"命令执行失败: {str(e)}", error=e
            )

    async def read_data(self) -> Any:
        """读取数据"""
        if not self.connected or not self.slave:
            raise Exception("设备未连接")

        try:
            # 读取所有配置的寄存器
            results = {}
            if self.config.registers:
                for register in self.config.registers:
                    result = await self.slave.execute(
                        register.get("function_code"),
                        register.get("address"),
                        register.get("count", 1),
                    )
                    results[register.get("name")] = result
            return results

        except Exception as e:
            self.last_error = e
            raise


class ModbusRtuDeviceConnection(DeviceConnection):
    """Modbus RTU设备连接"""

    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.master = None
        self.slave = None

    async def connect(self) -> bool:
        """连接设备"""
        try:
            self.master = modbus_rtu.RtuMaster(
                serial.Serial(
                    port=self.config.com_port,
                    baudrate=self.config.baudrate or 9600,
                    bytesize=self.config.bytesize or serial.EIGHTBITS,
                    parity=self.config.parity or serial.PARITY_NONE,
                    stopbits=self.config.stopbits or serial.STOPBITS_ONE,
                    timeout=self.config.timeout,
                )
            )
            self.slave = self.master.get_slave(self.config.slave_id or 1)
            self.connected = True
            return True
        except Exception as e:
            self.last_error = e
            return False

    async def disconnect(self):
        """断开连接"""
        if self.master:
            self.master.close()
            self.master = None
            self.slave = None
        self.connected = False

    async def send_command(self, command: DeviceCommand) -> CommandResult:
        """发送命令"""
        if not self.connected or not self.slave:
            return CommandResult(
                success=False, message="设备未连接", error=Exception("设备未连接")
            )

        try:
            func_code = getattr(cst, command.command, None)
            if not func_code:
                raise ValueError(f"无效的功能码: {command.command}")

            address = command.params.get("address", 0)
            data = command.params.get("data", [])

            result = await self.slave.execute(
                func_code, address, output_value=data if data else None
            )

            return CommandResult(success=True, message="命令执行成功", data=result)
        except Exception as e:
            self.last_error = e
            return CommandResult(
                success=False, message=f"命令执行失败: {str(e)}", error=e
            )

    async def read_data(self) -> Any:
        """读取数据"""
        if not self.connected or not self.slave:
            raise Exception("设备未连接")

        try:
            # 读取所有配置的寄存器
            results = {}
            if self.config.registers:
                for register in self.config.registers:
                    result = await self.slave.execute(
                        register.get("function_code"),
                        register.get("address"),
                        register.get("count", 1),
                    )
                    results[register.get("name")] = result
            return results

        except Exception as e:
            self.last_error = e
            raise


class SocketDeviceConnection(DeviceConnection):
    """Socket设备连接"""

    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.socket = None

    async def connect(self) -> bool:
        """连接设备"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.config.timeout)
            self.socket.connect((self.config.host, self.config.port))
            self.connected = True
            return True
        except Exception as e:
            self.last_error = e
            return False

    async def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False

    async def send_command(self, command: DeviceCommand) -> CommandResult:
        """发送命令"""
        if not self.connected or not self.socket:
            return CommandResult(
                success=False, message="设备未连接", error=Exception("设备未连接")
            )

        try:
            # 发送数据
            data = command.params.get("data", "").encode()
            await self.socket.send(data)

            # 接收响应
            response = await self.socket.recv(1024)

            return CommandResult(
                success=True, message="命令执行成功", data=response.decode()
            )
        except Exception as e:
            self.last_error = e
            return CommandResult(
                success=False, message=f"命令执行失败: {str(e)}", error=e
            )

    async def read_data(self) -> Any:
        """读取数据"""
        if not self.connected or not self.socket:
            raise Exception("设备未连接")

        try:
            data = await self.socket.recv(1024)
            return data.decode()
        except Exception as e:
            self.last_error = e
            raise


class SerialDeviceConnection(DeviceConnection):
    """串口设备连接"""

    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.serial = None

    async def connect(self) -> bool:
        """连接设备"""
        try:
            self.serial = serial.Serial(
                port=self.config.com_port,
                baudrate=self.config.baudrate or 9600,
                bytesize=self.config.bytesize or serial.EIGHTBITS,
                parity=self.config.parity or serial.PARITY_NONE,
                stopbits=self.config.stopbits or serial.STOPBITS_ONE,
                timeout=self.config.timeout,
            )
            self.connected = True
            return True
        except Exception as e:
            self.last_error = e
            return False

    async def disconnect(self):
        """断开连接"""
        if self.serial:
            self.serial.close()
            self.serial = None
        self.connected = False

    async def send_command(self, command: DeviceCommand) -> CommandResult:
        """发送命令"""
        if not self.connected or not self.serial:
            return CommandResult(
                success=False, message="设备未连接", error=Exception("设备未连接")
            )

        try:
            # 发送数据
            data = command.params.get("data", "").encode()
            self.serial.write(data)

            # 等待响应
            if command.timeout:
                self.serial.timeout = command.timeout
            response = self.serial.read_until()

            return CommandResult(
                success=True, message="命令执行成功", data=response.decode()
            )
        except Exception as e:
            self.last_error = e
            return CommandResult(
                success=False, message=f"命令执行失败: {str(e)}", error=e
            )

    async def read_data(self) -> Any:
        """读取数据"""
        if not self.connected or not self.serial:
            raise Exception("设备未连接")

        try:
            data = self.serial.read_until()
            return data.decode()
        except Exception as e:
            self.last_error = e
            raise


class DeviceManager:
    """设备管理器"""

    def __init__(self):
        self.devices: Dict[str, DeviceConnection] = {}
        self.device_status: Dict[str, Dict] = {}

    def register_device(self, config: DeviceConfig) -> bool:
        """注册设备"""
        try:
            if config.device_id in self.devices:
                return False

            # 根据设备类型创建连接
            if config.type == DeviceType.HTTP:
                connection = HttpDeviceConnection(config)
            elif config.type == DeviceType.MODBUS_TCP:
                connection = ModbusTcpDeviceConnection(config)
            elif config.type == DeviceType.MODBUS_RTU:
                connection = ModbusRtuDeviceConnection(config)
            elif config.type == DeviceType.SOCKET:
                connection = SocketDeviceConnection(config)
            elif config.type == DeviceType.SERIAL:
                connection = SerialDeviceConnection(config)
            else:
                return False

            self.devices[config.device_id] = connection
            self.device_status[config.device_id] = {
                "status": DeviceStatus.OFFLINE,
                "last_error": None,
                "last_update": datetime.now(),
            }
            return True
        except Exception:
            return False

    def unregister_device(self, device_id: str):
        """注销设备"""
        if device_id in self.devices:
            del self.devices[device_id]
        if device_id in self.device_status:
            del self.device_status[device_id]

    async def connect_device(self, device_id: str) -> bool:
        """连接设备"""
        device = self.devices.get(device_id)
        if not device:
            return False

        success = await device.connect()
        if success:
            self.device_status[device_id]["status"] = DeviceStatus.ONLINE
        return success

    async def disconnect_device(self, device_id: str):
        """断开设备连接"""
        device = self.devices.get(device_id)
        if device:
            await device.disconnect()
            self.device_status[device_id]["status"] = DeviceStatus.OFFLINE

    async def send_command(
        self, device_id: str, command: DeviceCommand
    ) -> CommandResult:
        """发送设备命令"""
        device = self.devices.get(device_id)
        if not device:
            return CommandResult(
                success=False, message="设备不存在", error=Exception("设备不存在")
            )

        result = await device.send_command(command)
        if not result.success:
            self.device_status[device_id]["last_error"] = result.error
        self.device_status[device_id]["last_update"] = datetime.now()
        return result

    async def read_device_data(self, device_id: str) -> Any:
        """读取设备数据"""
        device = self.devices.get(device_id)
        if not device:
            raise Exception("设备不存在")

        return await device.read_data()

    def get_device_status(self, device_id: str) -> Optional[Dict]:
        """获取设备状态"""
        status = self.device_status.get(device_id)
        if not status:
            return None

        device = self.devices.get(device_id)
        if device:
            return {
                "device_id": device_id,
                "name": device.config.name,
                "type": device.config.type.value,
                "status": status["status"].value,
                "connected": device.connected,
                "last_error": (
                    str(status["last_error"]) if status["last_error"] else None
                ),
                "last_update": status["last_update"].isoformat(),
            }
        return None

    def get_all_devices(self) -> List[Dict]:
        """获取所有设备状态"""
        return [
            self.get_device_status(device_id)
            for device_id in self.devices.keys()
            if self.get_device_status(device_id)
        ]
