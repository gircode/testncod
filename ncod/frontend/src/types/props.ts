import type { DeviceInfo } from './device'

export interface DeviceConnectorProps {
  device: DeviceInfo
  visible: boolean
}

export interface ExportProgressProps {
  visible: boolean
  taskId?: string
}

export interface StatsCardProps {
  title: string
  value: number | string
  trend?: number
  valueColor?: string
} 