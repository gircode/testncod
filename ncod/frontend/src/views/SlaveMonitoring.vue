import { formatDateTimeString, formatBytes, formatPercentage } from '@/utils/format'

const now = formatDateTimeString(new Date())

<span>{{ formatPercentage(item.cpuUsage) }}</span> 