export const storage = {
  get(key: string): any {
    const value = localStorage.getItem(key)
    if (value) {
      try {
        return JSON.parse(value)
      } catch {
        return value
      }
    }
    return null
  },

  set(key: string, value: any): void {
    if (typeof value === 'object') {
      localStorage.setItem(key, JSON.stringify(value))
    } else {
      localStorage.setItem(key, value)
    }
  },

  remove(key: string): void {
    localStorage.removeItem(key)
  },

  clear(): void {
    localStorage.clear()
  }
} 