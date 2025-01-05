import { ref, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'

export function useWebSocket({ onMessage, onError }) {
  const store = useStore()
  const ws = ref(null)
  const isConnected = ref(false)
  
  const connect = () => {
    const token = store.state.user.token
    const wsUrl = `${process.env.VUE_APP_WS_API}/monitor/ws?token=${token}`
    
    ws.value = new WebSocket(wsUrl)
    
    ws.value.onopen = () => {
      isConnected.value = true
      console.log('WebSocket连接已建立')
    }
    
    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage && onMessage(data)
      } catch (error) {
        console.error('处理WebSocket消息失败:', error)
      }
    }
    
    ws.value.onerror = (error) => {
      console.error('WebSocket错误:', error)
      onError && onError(error)
    }
    
    ws.value.onclose = () => {
      isConnected.value = false
      console.log('WebSocket连接已关闭')
      // 尝试重新连接
      setTimeout(connect, 5000)
    }
  }
  
  const close = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }
  
  const send = (message) => {
    if (ws.value && isConnected.value) {
      ws.value.send(JSON.stringify(message))
    }
  }
  
  onMounted(() => {
    connect()
  })
  
  onUnmounted(() => {
    close()
  })
  
  return {
    isConnected,
    send,
    close
  }
} 