export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T> {
  total: number
  items: T[]
}

export interface DeviceListResponse extends PaginatedResponse<DeviceInfo> {}

export interface DeviceStatsResponse {
  device_id: string
  stats: DeviceStats
  usage: DeviceUsage
}

export interface ExportTask {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
  file_url?: string
}

export interface ExportTaskResponse {
  task_id: string
  status: ExportTask['status']
}

export interface ExportParams {
  organization_id: number
  start_date: string
  end_date: string
  format: 'xlsx' | 'csv'
} 