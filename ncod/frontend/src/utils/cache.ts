interface CacheOptions {
  ttl?: number // 过期时间（毫秒）
  storage?: 'memory' | 'local' // 存储类型
}

interface CacheItem<T> {
  value: T
  timestamp: number
  ttl: number
}

class Cache {
  private memoryCache: Map<string, CacheItem<any>> = new Map()
  private prefix: string = 'ncod_cache_'

  constructor() {
    // 定期清理过期缓存
    setInterval(() => {
      this.cleanup()
    }, 60000) // 每分钟清理一次
  }

  /**
   * 设置缓存
   * @param key 缓存键
   * @param value 缓存值
   * @param options 缓存选项
   */
  set<T>(key: string, value: T, options: CacheOptions = {}) {
    const { ttl = 3600000, storage = 'memory' } = options // 默认1小时过期
    const item: CacheItem<T> = {
      value,
      timestamp: Date.now(),
      ttl
    }

    if (storage === 'memory') {
      this.memoryCache.set(key, item)
    } else {
      try {
        localStorage.setItem(this.prefix + key, JSON.stringify(item))
      } catch (error) {
        console.error('Failed to save to localStorage:', error)
        // 如果localStorage失败，回退到内存缓存
        this.memoryCache.set(key, item)
      }
    }
  }

  /**
   * 获取缓存
   * @param key 缓存键
   * @param defaultValue 默认值
   */
  get<T>(key: string, defaultValue?: T): T | undefined {
    // 先尝试从内存缓存获取
    const memoryItem = this.memoryCache.get(key)
    if (memoryItem && !this.isExpired(memoryItem)) {
      return memoryItem.value
    }

    // 再尝试从localStorage获取
    try {
      const localItem = localStorage.getItem(this.prefix + key)
      if (localItem) {
        const item: CacheItem<T> = JSON.parse(localItem)
        if (!this.isExpired(item)) {
          return item.value
        }
        // 如果已过期，删除它
        this.remove(key)
      }
    } catch (error) {
      console.error('Failed to read from localStorage:', error)
    }

    return defaultValue
  }

  /**
   * 删除缓存
   * @param key 缓存键
   */
  remove(key: string) {
    this.memoryCache.delete(key)
    try {
      localStorage.removeItem(this.prefix + key)
    } catch (error) {
      console.error('Failed to remove from localStorage:', error)
    }
  }

  /**
   * 清空所有缓存
   */
  clear() {
    this.memoryCache.clear()
    try {
      Object.keys(localStorage)
        .filter(key => key.startsWith(this.prefix))
        .forEach(key => localStorage.removeItem(key))
    } catch (error) {
      console.error('Failed to clear localStorage:', error)
    }
  }

  /**
   * 检查缓存是否存在且未过期
   * @param key 缓存键
   */
  has(key: string): boolean {
    return !!(
      (this.memoryCache.has(key) && !this.isExpired(this.memoryCache.get(key)!)) ||
      (localStorage.getItem(this.prefix + key) &&
        !this.isExpired(JSON.parse(localStorage.getItem(this.prefix + key)!)))
    )
  }

  /**
   * 获取所有缓存键
   */
  keys(): string[] {
    const memoryKeys = Array.from(this.memoryCache.keys())
    const localKeys = Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .map(key => key.slice(this.prefix.length))
    return Array.from(new Set([...memoryKeys, ...localKeys]))
  }

  /**
   * 清理过期缓存
   */
  private cleanup() {
    // 清理内存缓存
    for (const [key, item] of this.memoryCache.entries()) {
      if (this.isExpired(item)) {
        this.memoryCache.delete(key)
      }
    }

    // 清理localStorage缓存
    try {
      Object.keys(localStorage)
        .filter(key => key.startsWith(this.prefix))
        .forEach(key => {
          const item: CacheItem<any> = JSON.parse(localStorage.getItem(key)!)
          if (this.isExpired(item)) {
            localStorage.removeItem(key)
          }
        })
    } catch (error) {
      console.error('Failed to cleanup localStorage:', error)
    }
  }

  /**
   * 检查缓存项是否过期
   * @param item 缓存项
   */
  private isExpired(item: CacheItem<any>): boolean {
    return Date.now() - item.timestamp > item.ttl
  }
}

export default new Cache() 