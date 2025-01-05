import { defineStore } from 'pinia'
import type {
  Device,
  DeviceStatus,
  DeviceUsage,
  SlaveServer,
  DeviceForm,
  DeviceListResponse,
  DeviceStatusResponse,
  DeviceUsageResponse,
  SlaveListResponse,
  ApiResponse
} from '@/types/device'
import request from '@/utils/request'

interface DeviceState {
  device: Device | null
  deviceList: Device[]
  statusHistory: DeviceStatus[]
  usageHistory: DeviceUsage[]
  slaveList: SlaveServer[]
  loading: boolean
  total: number
}

export const useDeviceStore = defineStore('device', {
  state: (): DeviceState => ({
    device: null,
    deviceList: [],
    statusHistory: [],
    usageHistory: [],
    slaveList: [],
    loading: false,
    total: 0,
  }),

  actions: {
    async getDeviceList(params: any) {
      this.loading = true
      try {
        const response = await request.get<ApiResponse<DeviceListResponse>>('/api/devices', { params })
        this.deviceList = response.data.data
        this.total = response.data.total || 0
        return response.data
      } finally {
        this.loading = false
      }
    },

    async getDeviceDetail(id: number) {
      this.loading = true
      try {
        const response = await request.get<ApiResponse<Device>>(`/api/devices/${id}`)
        this.device = response.data.data
        return response.data.data
      } finally {
        this.loading = false
      }
    },

    async getDeviceStatusHistory(id: number, params: any) {
      this.loading = true
      try {
        const response = await request.get<ApiResponse<DeviceStatusResponse>>(`/api/devices/${id}/status-history`, { params })
        this.statusHistory = response.data.data.data
        return response.data.data
      } finally {
        this.loading = false
      }
    },

    async getDeviceUsageHistory(id: number, params: any) {
      this.loading = true
      try {
        const response = await request.get<ApiResponse<DeviceUsageResponse>>(`/api/devices/${id}/usage-history`, { params })
        this.usageHistory = response.data.data.data
        return response.data.data
      } finally {
        this.loading = false
      }
    },

    async getSlaveList() {
      this.loading = true
      try {
        const response = await request.get<ApiResponse<SlaveListResponse>>('/api/slaves')
        this.slaveList = response.data.data.data
        return response.data.data
      } finally {
        this.loading = false
      }
    },

    async createDevice(data: DeviceForm) {
      this.loading = true
      try {
        const response = await request.post<ApiResponse<Device>>('/api/devices', data)
        await this.getDeviceList({})
        return response.data
      } finally {
        this.loading = false
      }
    },

    async updateDevice(id: number, data: Partial<DeviceForm>) {
      this.loading = true
      try {
        const response = await request.put<ApiResponse<Device>>(`/api/devices/${id}`, data)
        await this.getDeviceDetail(id)
        return response.data
      } finally {
        this.loading = false
      }
    },

    async deleteDevice(id: number) {
      this.loading = true
      try {
        const response = await request.delete<ApiResponse<void>>(`/api/devices/${id}`)
        await this.getDeviceList({})
        return response.data
      } finally {
        this.loading = false
      }
    },
  },
}) 