export const logs = [
  {
    id: 1,
    type: 'info',
    module: 'auth',
    action: 'login',
    user_id: 1,
    username: 'admin',
    message: '管理员登录系统',
    ip_address: '192.168.1.100',
    created_at: '2024-01-04T09:00:00Z'
  },
  {
    id: 2,
    type: 'warning',
    module: 'device',
    action: 'status_change',
    user_id: null,
    username: 'system',
    message: '设备离线：USB加密狗',
    ip_address: '192.168.1.102',
    created_at: '2024-01-04T09:30:00Z'
  },
  {
    id: 3,
    type: 'error',
    module: 'slave',
    action: 'connection_lost',
    user_id: null,
    username: 'system',
    message: '从服务器2连接断开',
    ip_address: '192.168.1.102',
    created_at: '2024-01-04T09:45:00Z'
  }
] 