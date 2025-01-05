export interface SlaveMetrics {
  cpuUsage: number
  memoryUsage: number
  deviceCount: number
  onlineDevices: number
  occupiedDevices: number
  offlineDevices: number
  networkTraffic: number
  uploadTraffic: number
  downloadTraffic: number
}

export interface MetricsChartData {
  timestamp: string
  value: number
}

export interface SlaveMetricsResponse {
  currentMetrics: SlaveMetrics
  historicalMetrics: {
    cpu: MetricsChartData[]
    memory: MetricsChartData[]
    network: MetricsChartData[]
    devices: MetricsChartData[]
  }
} 