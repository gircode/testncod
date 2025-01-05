# NCOD API 文档

## 认证

所有API请求需要在Header中携带JWT Token:

```http
Authorization: Bearer <token>
```

## 设备管理API

### 获取设备列表

GET /api/v1/devices

参数:

- organization_id: 组织ID(可选)
- status: 设备状态(可选)

响应:

```json
{
  "total": 100,
  "items": [
    {
      "id": "device-001",
      "name": "Device 1",
      "status": "online",
      "organization_id": "org-001"
    }
  ]
}
```

### 批量操作设备

POST /api/v1/devices/batch

请求体:

```json
{
  "device_ids": ["device-001", "device-002"],
  "action": "update_status",
  "params": {
    "status": "disabled"
  }
}
```

响应:

```json
{
  "success": ["device-001"],
  "failed": ["device-002"]
}
```

## 设备批量操作

### 批量更新状态

POST /api/v1/devices/batch/status

请求体:

```json
{
  "device_ids": ["device-001", "device-002"],
  "status": "disabled"
}
```

### 批量分配组织

POST /api/v1/devices/batch/organization

请求体:

```json
{
  "device_ids": ["device-001", "device-002"],
  "organization_id": "org-001"
}
```

### 批量删除设备

POST /api/v1/devices/batch/delete

请求体:

```json
{
  "device_ids": ["device-001", "device-002"]
}
```

响应格式:

```json
{
  "success": ["device-001"],
  "failed": ["device-002"],
  "total": 2,
  "success_count": 1,
  "failed_count": 1
}
```
