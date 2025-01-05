import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  data: string;
  type: string;
  timestamp: string;
}

interface UseWebSocketReturn {
  lastMessage: WebSocketMessage | null;
  sendMessage: (data: any) => void;
  readyState: number;
}

export const useWebSocket = (type: string): UseWebSocketReturn => {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const ws = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    // 创建WebSocket连接
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/${type}`;
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onopen = () => {
      console.log('WebSocket连接已建立');
      setReadyState(WebSocket.OPEN);
    };
    
    ws.current.onclose = () => {
      console.log('WebSocket连接已关闭');
      setReadyState(WebSocket.CLOSED);
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket错误:', error);
      setReadyState(WebSocket.CLOSED);
    };
    
    ws.current.onmessage = (event) => {
      const message: WebSocketMessage = {
        data: event.data,
        type: type,
        timestamp: new Date().toISOString()
      };
      setLastMessage(message);
    };
    
    // 清理函数
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [type]);
  
  const sendMessage = (data: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    } else {
      console.error('WebSocket未连接');
    }
  };
  
  return {
    lastMessage,
    sendMessage,
    readyState
  };
}; 