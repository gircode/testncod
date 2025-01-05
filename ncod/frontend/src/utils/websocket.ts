import { ref } from 'vue'

interface WebSocketOptions {
    url: string
    onMessage?: (data: any) => void
    onOpen?: () => void
    onClose?: () => void
    onError?: (error: Event) => void
    reconnectInterval?: number
    maxReconnectAttempts?: number
}

export function useWebSocket(options: WebSocketOptions) {
    const {
        url,
        onMessage,
        onOpen,
        onClose,
        onError,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5
    } = options

    let ws: WebSocket | null = null
    let reconnectCount = 0
    let reconnectTimer: number | null = null

    const isConnected = ref(false)
    const lastError = ref<Event | null>(null)

    function connect() {
        ws = new WebSocket(url)

        ws.onopen = () => {
            isConnected.value = true
            reconnectCount = 0
            onOpen?.()
        }

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                onMessage?.(data)
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error)
            }
        }

        ws.onclose = () => {
            isConnected.value = false
            onClose?.()
            reconnect()
        }

        ws.onerror = (error) => {
            lastError.value = error
            onError?.(error)
        }
    }

    function reconnect() {
        if (reconnectCount >= maxReconnectAttempts) {
            console.error('Max reconnection attempts reached')
            return
        }

        if (reconnectTimer) {
            window.clearTimeout(reconnectTimer)
        }

        reconnectTimer = window.setTimeout(() => {
            reconnectCount++
            connect()
        }, reconnectInterval)
    }

    function send(data: any) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected')
            return
        }

        try {
            ws.send(JSON.stringify(data))
        } catch (error) {
            console.error('Failed to send WebSocket message:', error)
        }
    }

    function close() {
        if (reconnectTimer) {
            window.clearTimeout(reconnectTimer)
        }

        if (ws) {
            ws.close()
            ws = null
        }
    }

    // 初始连接
    connect()

    return {
        isConnected,
        lastError,
        send,
        close
    }
} 