export const devices = [
  {
    id: 1,
    name: 'USB打印机',
    type: 'printer',
    slave_id: 1,
    slave_name: '从服务器1',
    status: 'online',
    vendor_id: '0483',
    product_id: '5740',
    serial_number: 'PRINTER001',
    description: '办公室打印机',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: 'USB扫描仪',
    type: 'scanner',
    slave_id: 1,
    slave_name: '从服务器1',
    status: 'in_use',
    vendor_id: '04B8',
    product_id: '013C',
    serial_number: 'SCANNER001',
    description: '文档扫描仪',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z'
  },
  {
    id: 3,
    name: 'USB加密狗',
    type: 'dongle',
    slave_id: 2,
    slave_name: '从服务器2',
    status: 'offline',
    vendor_id: '096E',
    product_id: '0006',
    serial_number: 'DONGLE001',
    description: '软件加密狗',
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z'
  }
]

export const deviceStatus = [
  {
    id: 1,
    device_id: 1,
    status: 'online',
    cpu_usage: 0.2,
    memory_usage: 0.3,
    disk_usage: 0.1,
    recorded_at: '2024-01-04T10:00:00Z'
  },
  {
    id: 2,
    device_id: 2,
    status: 'in_use',
    cpu_usage: 0.5,
    memory_usage: 0.4,
    disk_usage: 0.2,
    recorded_at: '2024-01-04T10:00:00Z'
  },
  {
    id: 3,
    device_id: 3,
    status: 'offline',
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    recorded_at: '2024-01-04T10:00:00Z'
  }
]

export const deviceUsage = [
  {
    id: 1,
    device_id: 1,
    user_id: 2,
    user_name: 'user1',
    start_time: '2024-01-04T09:00:00Z',
    end_time: '2024-01-04T10:00:00Z',
    description: '打印文档'
  },
  {
    id: 2,
    device_id: 2,
    user_id: 2,
    user_name: 'user1',
    start_time: '2024-01-04T10:00:00Z',
    end_time: null,
    description: '扫描文件'
  }
] 