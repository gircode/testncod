import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore'
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter'

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.extend(isSameOrBefore)
dayjs.extend(isSameOrAfter)
dayjs.locale('zh-cn')

export function formatDate(date: string | number | Date): string {
  return dayjs(date).format('YYYY-MM-DD')
}

export function formatDateTime(date: string | number | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

export function formatTime(date: string | number | Date): string {
  return dayjs(date).format('HH:mm:ss')
}

export function fromNow(date: string | number | Date): string {
  return dayjs(date).fromNow()
}

export function getDateRange(type: 'today' | 'week' | 'month' | 'year') {
  const end = dayjs()
  let start: dayjs.Dayjs

  switch (type) {
    case 'today':
      start = end.startOf('day')
      break
    case 'week':
      start = end.startOf('week')
      break
    case 'month':
      start = end.startOf('month')
      break
    case 'year':
      start = end.startOf('year')
      break
  }

  return {
    start: start.format('YYYY-MM-DD HH:mm:ss'),
    end: end.format('YYYY-MM-DD HH:mm:ss')
  }
}

export function isDateBetween(
  date: string | number | Date,
  start: string | number | Date,
  end: string | number | Date
): boolean {
  const d = dayjs(date)
  return d.isSameOrAfter(start) && d.isSameOrBefore(end)
}

export function addDays(date: string | number | Date, days: number): string {
  return dayjs(date).add(days, 'day').format('YYYY-MM-DD')
}

export function subtractDays(date: string | number | Date, days: number): string {
  return dayjs(date).subtract(days, 'day').format('YYYY-MM-DD')
}

export function getDaysDiff(
  start: string | number | Date,
  end: string | number | Date
): number {
  return dayjs(end).diff(dayjs(start), 'day')
}

export function isToday(date: string | number | Date): boolean {
  return dayjs(date).isSame(dayjs(), 'day')
}

export function isYesterday(date: string | number | Date): boolean {
  return dayjs(date).isSame(dayjs().subtract(1, 'day'), 'day')
}

export function isTomorrow(date: string | number | Date): boolean {
  return dayjs(date).isSame(dayjs().add(1, 'day'), 'day')
}

export function isThisWeek(date: string | number | Date): boolean {
  return dayjs(date).isSame(dayjs(), 'week')
}

export function isThisMonth(date: string | number | Date): boolean {
  return dayjs(date).isSame(dayjs(), 'month')
}

export function isThisYear(date: string | number | Date): boolean {
  return dayjs(date).isSame(dayjs(), 'year')
} 