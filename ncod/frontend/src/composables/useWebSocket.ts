import { ref } from 'vue'

interface WebSocketOptions {
  url: string
  onMessage?: (data: any) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
  autoReconnect?: boolean
}

interface WebSocketInstance {
  isConnected: Ref<boolean>
  lastError: Ref<Event | null>
  send: (data: any) => void
  close: () => void
  connect: () => void
  subscribe: (event: string, callback: (data: any) => void) => void
  unsubscribe: (event: string) => void
}

export function useWebSocket(options: WebSocketOptions): WebSocketInstance {
  const {
    url,
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    autoReconnect = true
  } = options

  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const lastError = ref<Event | null>(null)
  const reconnectCount = ref(0)
  const reconnectTimer = ref<number | null>(null)
  const eventHandlers = new Map<string, Set<(data: any) => void>>()

  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return
    }

    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      isConnected.value = true
      reconnectCount.value = 0
      onOpen?.()
    }

    ws.value.onclose = () => {
      isConnected.value = false
      onClose?.()
      if (autoReconnect) {
        reconnect()
      }
    }

    ws.value.onerror = (error: Event) => {
      lastError.value = error
      onError?.(error)
    }

    ws.value.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        if (data.event && eventHandlers.has(data.event)) {
          eventHandlers.get(data.event)?.forEach(handler => handler(data.data))
        }
        onMessage?.(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
  }

  const reconnect = () => {
    if (reconnectCount.value >= maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    if (reconnectTimer.value) {
      window.clearTimeout(reconnectTimer.value)
    }

    reconnectTimer.value = window.setTimeout(() => {
      reconnectCount.value++
      connect()
    }, reconnectInterval)
  }

  const send = (data: any) => {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected')
      return
    }

    try {
      ws.value.send(JSON.stringify(data))
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
    }
  }

  const close = () => {
    if (reconnectTimer.value) {
      window.clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }

    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  const subscribe = (event: string, callback: (data: any) => void) => {
    if (!eventHandlers.has(event)) {
      eventHandlers.set(event, new Set())
    }
    eventHandlers.get(event)?.add(callback)
  }

  const unsubscribe = (event: string) => {
    eventHandlers.delete(event)
  }

  // 初始连接
  connect()

  return {
    isConnected,
    lastError,
    send,
    close,
    connect,
    subscribe,
    unsubscribe
  }
} 