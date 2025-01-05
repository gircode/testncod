declare module '@/types/device' {
  export interface Device {
    id: number;
    name: string;
    type: string;
    slave_id: number;
    slave_name: string;
    status: 'online' | 'offline' | 'in_use';
    description?: string;
    created_at: string;
    updated_at: string;
  }

  export interface DeviceStatus {
    id: number;
    device_id: number;
    status: string;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    recorded_at: string;
  }

  export interface DeviceUsage {
    id: number;
    device_id: number;
    user_id: number;
    user_name: string;
    start_time: string;
    end_time: string;
    description?: string;
  }

  export interface SlaveServer {
    id: number;
    name: string;
    host: string;
    port: number;
    status: 'online' | 'offline';
  }

  export interface DeviceForm {
    id?: number;
    name: string;
    type: string;
    slave_id: number | undefined;
    description?: string;
  }

  export interface DeviceSearchParams {
    name?: string;
    type?: string;
    status?: string;
    page?: number;
    pageSize?: number;
  }

  export interface DeviceListResponse {
    data: Device[];
    total: number;
  }

  export interface DeviceStatusResponse {
    data: DeviceStatus[];
    total: number;
  }

  export interface DeviceUsageResponse {
    data: DeviceUsage[];
    total: number;
  }

  export interface SlaveListResponse {
    data: SlaveServer[];
    total: number;
  }

  export interface ApiResponse<T> {
    code: number;
    message: string;
    data: T;
    total?: number;
  }
} 