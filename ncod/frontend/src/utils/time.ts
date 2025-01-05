import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.locale('zh-cn')

export function formatDateTime(date: string | number | Date): string {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

export function formatDate(date: string | number | Date): string {
    return dayjs(date).format('YYYY-MM-DD')
}

export function formatTime(date: string | number | Date): string {
    return dayjs(date).format('HH:mm:ss')
}

export function fromNow(date: string | number | Date): string {
    return dayjs(date).fromNow()
}

export function formatDuration(milliseconds: number): string {
    const duration = dayjs.duration(milliseconds)
    const hours = duration.hours()
    const minutes = duration.minutes()
    const seconds = duration.seconds()

    if (hours > 0) {
        return `${hours}小时${minutes}分钟`
    } else if (minutes > 0) {
        return `${minutes}分钟${seconds}秒`
    } else {
        return `${seconds}秒`
    }
}

export function getTimeRange(type: 'today' | 'week' | 'month' | 'year') {
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

export function parseTimeRange(range: [Date, Date]) {
    return {
        start: dayjs(range[0]).format('YYYY-MM-DD HH:mm:ss'),
        end: dayjs(range[1]).format('YYYY-MM-DD HH:mm:ss')
    }
} 