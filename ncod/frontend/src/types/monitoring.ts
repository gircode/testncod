// 服务器基础信息类型
export interface ServerInfo {
  id: string;
  name: string;
  version: string;
  uptime: number;
  os: string;
  arch: string;
  cpu_cores: number;
  memory_total: number;
  disk_total: number;
}

// 系统指标类型
export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_in: number;
  network_out: number;
  uptime: number;
  process_count: number;
  timestamp: string;
}

// 设备统计信息
export interface DeviceStats {
  type: string;
  total: number;
  active: number;
  inactive: number;
  error: number;
}

// 告警类型
export interface Alert {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'critical';
  type: string;
  message: string;
  acknowledged: boolean;
}

// 进程状态类型
export interface ProcessStatus {
  running: number;
  sleeping: number;
  stopped: number;
  zombie: number;
}

// 系统负载类型
export interface SystemLoad {
  load1: number;
  load5: number;
  load15: number;
}

// 历史数据点类型
export interface MetricDataPoint {
  timestamp: number;
  value: number;
}

// 历史数据类型
export interface HistoricalMetrics {
  timestamps: string[];
  cpu_usage: number[];
  memory_usage: number[];
  disk_usage: number[];
  network_in: number[];
  network_out: number[];
} 