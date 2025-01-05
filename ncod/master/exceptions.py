from fastapi import HTTPException, status


class DeviceError(HTTPException):
    def __init__(
        self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        super().__init__(
            status_code=status_code, detail={"code": code, "message": message}
        )


class DeviceNotFoundError(DeviceError):
    def __init__(self, device_id: str):
        super().__init__(
            code="DEVICE_NOT_FOUND",
            message=f"Device {device_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class DeviceBusyError(DeviceError):
    def __init__(self, device_id: str):
        super().__init__(
            code="DEVICE_BUSY",
            message=f"Device {device_id} is currently in use",
            status_code=status.HTTP_409_CONFLICT,
        )


class DeviceOfflineError(DeviceError):
    def __init__(self, device_id: str):
        super().__init__(
            code="DEVICE_OFFLINE",
            message=f"Device {device_id} is offline",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class PermissionDeniedError(DeviceError):
    def __init__(self):
        super().__init__(
            code="PERMISSION_DENIED",
            message="Permission denied",
            status_code=status.HTTP_403_FORBIDDEN,
        )
