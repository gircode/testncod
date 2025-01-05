import { http } from '@/utils/http';

export interface DeviceCreate {
  name: string;
  mac_address: string;
  ip_address?: string;
  description?: string;
  organization_id?: string;
  slave_id?: string;
}

export interface DeviceUpdate {
  name?: string;
  mac_address?: string;
  ip_address?: string;
  description?: string;
  is_active?: boolean;
  organization_id?: string;
  slave_id?: string;
}

export const deviceApi = {
  // 创建设备
  createDevice(data: DeviceCreate) {
    return http.post('/api/v1/devices', data);
  },

  // 更新设备
  updateDevice(deviceId: string, data: DeviceUpdate) {
    return http.put(`/api/v1/devices/${deviceId}`, data);
  },

  // 删除设备
  deleteDevice(deviceId: string) {
    return http.delete(`/api/v1/devices/${deviceId}`);
  },

  // 获取设备
  getDevice(deviceId: string) {
    return http.get(`/api/v1/devices/${deviceId}`);
  },

  // 获取设备列表
  listDevices(params?: {
    organization_id?: string;
    slave_id?: string;
  }) {
    return http.get('/api/v1/devices', { params });
  }
}; 