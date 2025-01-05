/// <reference types="vite/client" />

declare module 'echarts/core'
declare module 'echarts/renderers'
declare module 'echarts/charts'
declare module 'echarts/components'

declare interface Window {
  echarts: typeof import('echarts')
}

declare type Nullable<T> = T | null

declare type TimeRange = '1h' | '6h' | '24h'

declare type StatusType = 'online' | 'offline' | 'error'

declare type MetricType = 'cpu' | 'memory' | 'disk' | 'network'

declare type AlertLevel = 'info' | 'warning' | 'error' | 'critical'

declare type AlertCondition = 'gt' | 'lt' | 'eq' | 'ne' | 'ge' | 'le' 