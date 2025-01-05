export interface User {
  id: number
  username: string
  role: string
  email: string
  organization: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginResponse {
  code: number
  message: string
  data: {
    token: string
    user: User
  } | null
}

export interface ListResponse<T> {
  code: number
  message: string
  data: {
    items: T[]
    total: number
  }
}

export interface Device {
  id: number
  name: string
  type: string
  slave_id: number
  slave_name: string
  status: string
  vendor_id: string
  product_id: string
  serial_number: string
  description: string
  created_at: string
  updated_at: string
}

export interface Slave {
  id: number
  name: string
  host: string
  port: number
  status: string
  mac_address: string
  last_heartbeat: string
  created_at: string
  updated_at: string
} 