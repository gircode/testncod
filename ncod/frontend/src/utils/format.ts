import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(duration)
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

// 格式化日期时间
export function formatDateTimeString(date: string | number | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 格式化字节大小
 * @param bytes 字节数
 * @param decimals 小数位数
 */
export const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

/**
 * 格式化百分比
 * @param value 小数值
 * @param decimals 小数位数
 */
export const formatPercentage = (value?: number) => {
  if (typeof value !== 'number') return '-'
  return `${(value * 100).toFixed(2)}%`
}

// 格式化比特率
export function formatBitrate(bits: number): string {
  if (bits === 0) return '0 bps'
  const k = 1000
  const sizes = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
  const i = Math.floor(Math.log(bits) / Math.log(k))
  return parseFloat((bits / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化持续时间（秒）
 * @param seconds 秒数
 */
export const formatDurationSeconds = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}秒`
  }
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}分${remainingSeconds}秒`
  }
  if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分`
  }
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  return `${days}天${hours}小时`
}

// 格式化持续时间（毫秒）
export function formatDurationMillis(millis: number): string {
  return formatDurationSeconds(millis / 1000)
}

// 格式化温度
export function formatTemperature(celsius: number): string {
  return `${celsius.toFixed(1)}°C`
}

// 格式化 IOPS
export function formatIOPS(iops: number): string {
  if (iops === 0) return '0 IOPS'
  const k = 1000
  const sizes = ['IOPS', 'KIOPS', 'MIOPS', 'GIOPS']
  const i = Math.floor(Math.log(iops) / Math.log(k))
  return parseFloat((iops / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化数字
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('zh-CN').format(num)
}

/**
 * 格式化日期
 * @param date 日期时间字符串或Date对象
 */
export const formatDate = (date?: string) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 格式化时间
 * @param date 日期时间字符串或Date对象
 */
export const formatTime = (date: string | Date): string => {
  const d = typeof date === 'string' ? new Date(date) : date
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return `${hours}:${minutes}:${seconds}`
}

export const formatDuration = (startTime?: string, endTime?: string) => {
  if (!startTime || !endTime) return '-'
  const start = dayjs(startTime)
  const end = dayjs(endTime)
  const diff = end.diff(start)
  return dayjs.duration(diff).humanize()
} 