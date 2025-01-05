import request from '@/utils/request'

export interface CacheInfo {
  size: number
  keys: number
  hits: number
  misses: number
  hitRate: number
  expiryTime: number
  lastCleanTime: string
}

export interface CacheStats {
  total: {
    size: number
    keys: number
    hits: number
    misses: number
    hitRate: number
  }
  caches: Record<string, CacheInfo>
}

export interface SystemInfo {
  os: {
    platform: string
    release: string
    arch: string
  }
  cpu: {
    model: string
    cores: number
    usage: number
  }
  memory: {
    total: number
    used: number
    free: number
    usage: number
  }
  disk: {
    total: number
    used: number
    free: number
    usage: number
  }
  python: {
    version: string
    implementation: string
  }
  uptime: number
  startTime: string
}

/**
 * 获取缓存统计信息
 */
export const getCacheStats = () => {
  return request.get<CacheStats>('/admin/cache/stats')
}

/**
 * 清理指定类型或所有缓存
 * @param type 缓存类型，不传则清理所有缓存
 */
export const clearCache = (type?: string) => {
  return request.post('/admin/cache/clear', { type })
}

/**
 * 获取系统信息
 */
export const getSystemInfo = () => {
  return request.get<SystemInfo>('/admin/system/info')
}

/**
 * 执行系统维护任务
 */
export const performMaintenance = () => {
  return request.post('/admin/system/maintenance')
} 