// 用户数据
export const users = [
  {
    id: 1,
    username: 'admin',
    password: '123456',
    email: 'admin@example.com',
    role: 'admin',
    organization: '系统管理部',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    username: 'user1',
    password: '123456',
    email: 'user1@example.com',
    role: 'user',
    organization: '研发部',
    mac_address: '00:11:22:33:44:55',
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z'
  }
]

// 设备数据
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
  }
]

// 从服务器数据
export const slaves = [
  {
    id: 1,
    name: '从服务器1',
    host: '192.168.1.101',
    port: 8001,
    status: 'online',
    mac_address: 'CC:DD:EE:FF:00:11',
    last_heartbeat: '2024-01-04T10:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: '从服务器2',
    host: '192.168.1.102',
    port: 8001,
    status: 'offline',
    mac_address: 'CC:DD:EE:FF:00:22',
    last_heartbeat: '2024-01-03T10:00:00Z',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z'
  }
] 