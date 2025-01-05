import { ref } from 'vue'
import { useDeviceStore } from '@/store/device'

export class StatsWebSocket {
  private ws: WebSocket | null = null
  private pingInterval: number | null = null
  private reconnectAttempts = 0
  private readonly maxReconnectAttempts = 5
  
  constructor(private userId: number) {}
  
  connect() {
    try {
      this.ws = new WebSocket(`ws://${window.location.host}/api/v1/ws/stats/${this.userId}`)
      
      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
      this.ws.onerror = this.handleError.bind(this)
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }
  
  private handleOpen() {
    console.log('Stats WebSocket connected')
    this.reconnectAttempts = 0
    this.startPing()
  }
  
  private handleMessage(event: MessageEvent) {
    const data = JSON.parse(event.data)
    
    if (data.type === 'stats_update') {
      this.handleStatsUpdate(data.data)
    }
  }
  
  private handleStatsUpdate(data: any) {
    const deviceStore = useDeviceStore()
    deviceStore.updateDeviceStats(data.device_id, data)
  }
  
  private handleClose() {
    this.stopPing()
    this.reconnect()
  }
  
  private handleError(error: Event) {
    console.error('WebSocket error:', error)
  }
  
  private startPing() {
    this.pingInterval = window.setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000)
  }
  
  private stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }
  
  private send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
  
  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }
    
    this.reconnectAttempts++
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
    
    console.log(`Reconnecting in ${delay}ms... Attempt ${this.reconnectAttempts}`)
    setTimeout(() => this.connect(), delay)
  }
  
  disconnect() {
    this.stopPing()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

// 创建单例
let statsWsInstance: StatsWebSocket | null = null

export function useStatsWebSocket(userId: number) {
  if (!statsWsInstance) {
    statsWsInstance = new StatsWebSocket(userId)
  }
  return statsWsInstance
} 