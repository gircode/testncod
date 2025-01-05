import axios from 'axios'
import type { MasterServer, SlaveServer, ServerPerformance, ServerMetrics } from '@/types/server'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 5000
})

// 错误处理拦截器
api.interceptors.response.use(
    response => response,
    error => {
        const { response } = error
        if (response?.data?.message) {
            // TODO: 使用Element Plus的消息提示组件
            console.error(response.data.message)
        }
        return Promise.reject(error)
    }
)

export const serverApi = {
    // 获取主服务器状态
    getMasterStatus: () => api.get<MasterServer>('/server/master/status'),

    // 获取从服务器列表
    getSlaveServers: (params?: { page?: number; pageSize?: number }) =>
        api.get<{ total: number; items: SlaveServer[] }>('/server/slaves', { params }),

    // 获取服务器性能数据
    getServerPerformance: (serverId: string) =>
        api.get<ServerPerformance>(`/server/${serverId}/performance`),

    // 获取历史性能数据
    getPerformanceHistory: (serverId: string, timeRange: string) =>
        api.get<ServerPerformance[]>(`/server/${serverId}/performance/history`, {
            params: { timeRange }
        }),

    // 获取详细监控指标
    getServerMetrics: (serverId: string) =>
        api.get<ServerMetrics>(`/server/${serverId}/metrics`),

    // 批量操作服务器
    batchOperation: (
        operation: string,
        serverIds: string[],
        options?: {
            schedule?: 'immediate' | 'scheduled'
            scheduleTime?: string
            config?: {
                maxDevices: number
                autoLoadBalance: boolean
                loadThreshold: number
            }
            optimizeOptions?: string[]
        }
    ) => api.post('/server/batch', { operation, serverIds, ...options }),

    // 添加从服务器
    addSlaveServer: (data: Partial<SlaveServer>) =>
        api.post<SlaveServer>('/server/slaves', data),

    // 更新服务器配置
    updateServer: (serverId: string, data: Partial<SlaveServer>) =>
        api.put(`/server/${serverId}`, data),

    // 删除服务器
    deleteServer: (serverId: string) =>
        api.delete(`/server/${serverId}`),

    // 获取服务器日志
    getServerLogs: (params: {
        serverId?: string
        level?: string
        startTime?: string
        endTime?: string
        page?: number
        pageSize?: number
    }) => api.get('/server/logs', { params })
} 