import { createApp, h } from 'vue'

interface MessageOptions {
  type: 'success' | 'error' | 'warning' | 'info'
  content: string
  duration?: number
}

const Message = {
  show(options: MessageOptions) {
    const { type, content, duration = 3000 } = options
    
    // 创建消息容器
    const container = document.createElement('div')
    container.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 z-50 flex flex-col items-center space-y-2'
    
    // 检查是否已存在消息容器
    const existingContainer = document.querySelector('.message-container')
    if (existingContainer) {
      document.body.removeChild(existingContainer)
    }
    container.classList.add('message-container')
    document.body.appendChild(container)

    // 创建消息组件
    const MessageComponent = {
      props: {
        type: String,
        content: String,
      },
      setup(props: { type: string; content: string }) {
        const bgColorClass = {
          success: 'bg-green-500',
          error: 'bg-red-500',
          warning: 'bg-yellow-500',
          info: 'bg-blue-500'
        }[props.type]

        const iconPath = {
          success: 'M5 13l4 4L19 7',
          error: 'M6 18L18 6M6 6l12 12',
          warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
          info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
        }[props.type]

        return () => h('div', {
          class: `flex items-center space-x-2 px-4 py-2 rounded-lg text-white shadow-lg ${bgColorClass} transition-all duration-300 ease-in-out transform translate-y-0 opacity-100`,
        }, [
          h('svg', {
            class: 'w-5 h-5',
            fill: 'none',
            stroke: 'currentColor',
            viewBox: '0 0 24 24',
            'stroke-width': '2',
          }, [
            h('path', {
              'stroke-linecap': 'round',
              'stroke-linejoin': 'round',
              d: iconPath,
            }),
          ]),
          h('span', { class: 'text-sm font-medium' }, props.content),
        ])
      },
    }

    // 创建并挂载消息实例
    const messageApp = createApp(MessageComponent, {
      type,
      content,
    })
    
    const messageElement = document.createElement('div')
    container.appendChild(messageElement)
    messageApp.mount(messageElement)

    // 自动移除消息
    setTimeout(() => {
      messageApp.unmount()
      messageElement.remove()
      if (container.children.length === 0) {
        document.body.removeChild(container)
      }
    }, duration)
  },

  success(content: string, duration?: number) {
    this.show({ type: 'success', content, duration })
  },

  error(content: string, duration?: number) {
    this.show({ type: 'error', content, duration })
  },

  warning(content: string, duration?: number) {
    this.show({ type: 'warning', content, duration })
  },

  info(content: string, duration?: number) {
    this.show({ type: 'info', content, duration })
  },
}

export default Message 