import Logger from './logger'

interface PerformanceMetrics {
  pageLoadTime: number
  resourceLoadTime: number
  domContentLoadedTime: number
  firstPaintTime: number
  firstContentfulPaintTime: number
  largestContentfulPaintTime: number
  firstInputDelayTime: number
  cumulativeLayoutShift: number
  memoryUsage?: {
    jsHeapSizeLimit: number
    totalJSHeapSize: number
    usedJSHeapSize: number
  }
}

interface ResourceTiming {
  name: string
  initiatorType: string
  duration: number
  transferSize: number
  decodedBodySize: number
}

class PerformanceService {
  private static readonly PERFORMANCE_LOG_KEY = 'performance_metrics'
  private static readonly RESOURCE_THRESHOLD = 1000 // 1秒
  private static readonly MEMORY_THRESHOLD = 0.9 // 90%
  private static readonly FPS_THRESHOLD = 30

  private frameCount: number = 0
  private lastFrameTime: number = performance.now()
  private isMonitoring: boolean = false

  constructor() {
    this.setupPerformanceObservers()
    this.setupMemoryMonitoring()
    this.setupFPSMonitoring()
  }

  /**
   * 设置性能观察器
   */
  private setupPerformanceObservers() {
    // 观察绘制时间
    if ('PerformanceObserver' in window) {
      // 观察最大内容绘制时间
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries()
        const lastEntry = entries[entries.length - 1]
        Logger.info('performance', 'lcp', {
          time: lastEntry.startTime,
          element: (lastEntry as any).element
        })
      })
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })

      // 观察首次输入延迟
      const fidObserver = new PerformanceObserver((entryList) => {
        const firstInput = entryList.getEntries()[0]
        Logger.info('performance', 'fid', {
          time: firstInput.processingStart! - firstInput.startTime
        })
      })
      fidObserver.observe({ entryTypes: ['first-input'] })

      // 观察布局偏移
      const clsObserver = new PerformanceObserver((entryList) => {
        let clsValue = 0
        for (const entry of entryList.getEntries() as PerformanceEntry[]) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value
          }
        }
        Logger.info('performance', 'cls', { value: clsValue })
      })
      clsObserver.observe({ entryTypes: ['layout-shift'] })

      // 观察长任务
      const longTaskObserver = new PerformanceObserver((entryList) => {
        entryList.getEntries().forEach(entry => {
          Logger.warning('performance', 'long_task', {
            duration: entry.duration,
            startTime: entry.startTime
          })
        })
      })
      longTaskObserver.observe({ entryTypes: ['longtask'] })
    }
  }

  /**
   * 设置内存监控
   */
  private setupMemoryMonitoring() {
    if ((performance as any).memory) {
      setInterval(() => {
        const memory = (performance as any).memory
        const usage = memory.usedJSHeapSize / memory.jsHeapSizeLimit

        if (usage > PerformanceService.MEMORY_THRESHOLD) {
          Logger.warning('performance', 'high_memory_usage', {
            usage: usage * 100,
            used: memory.usedJSHeapSize,
            total: memory.jsHeapSizeLimit
          })
        }
      }, 10000) // 每10秒检查一次
    }
  }

  /**
   * 设置FPS监控
   */
  private setupFPSMonitoring() {
    const measureFPS = () => {
      this.frameCount++
      const currentTime = performance.now()
      const elapsed = currentTime - this.lastFrameTime

      if (elapsed >= 1000) { // 每秒计算一次
        const fps = (this.frameCount * 1000) / elapsed
        this.frameCount = 0
        this.lastFrameTime = currentTime

        if (fps < PerformanceService.FPS_THRESHOLD) {
          Logger.warning('performance', 'low_fps', { fps })
        }
      }

      if (this.isMonitoring) {
        requestAnimationFrame(measureFPS)
      }
    }

    this.isMonitoring = true
    requestAnimationFrame(measureFPS)
  }

  /**
   * 收集性能指标
   */
  public collectMetrics(): PerformanceMetrics {
    const timing = performance.timing
    const paint = performance.getEntriesByType('paint')
    const lcp = performance.getEntriesByType('largest-contentful-paint').pop()
    const fid = performance.getEntriesByType('first-input').pop()

    const metrics: PerformanceMetrics = {
      pageLoadTime: timing.loadEventEnd - timing.navigationStart,
      resourceLoadTime: timing.domComplete - timing.domLoading,
      domContentLoadedTime: timing.domContentLoadedEventEnd - timing.navigationStart,
      firstPaintTime: paint.find(entry => entry.name === 'first-paint')?.startTime || 0,
      firstContentfulPaintTime: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
      largestContentfulPaintTime: (lcp as any)?.startTime || 0,
      firstInputDelayTime: fid ? (fid as any).processingStart - (fid as any).startTime : 0,
      cumulativeLayoutShift: this.getCumulativeLayoutShift()
    }

    if ((performance as any).memory) {
      metrics.memoryUsage = {
        jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize
      }
    }

    return metrics
  }

  /**
   * 获取累积布局偏移
   */
  private getCumulativeLayoutShift(): number {
    let cls = 0
    const entries = performance.getEntriesByType('layout-shift')
    for (const entry of entries as PerformanceEntry[]) {
      if (!(entry as any).hadRecentInput) {
        cls += (entry as any).value
      }
    }
    return cls
  }

  /**
   * 分析资源加载性能
   */
  public analyzeResourcePerformance(): ResourceTiming[] {
    const resources = performance.getEntriesByType('resource')
    const slowResources = resources
      .filter(resource => resource.duration > PerformanceService.RESOURCE_THRESHOLD)
      .map(resource => ({
        name: resource.name,
        initiatorType: resource.initiatorType,
        duration: resource.duration,
        transferSize: resource.transferSize,
        decodedBodySize: resource.decodedBodySize
      }))

    if (slowResources.length > 0) {
      Logger.warning('performance', 'slow_resources', { resources: slowResources })
    }

    return slowResources
  }

  /**
   * 清理性能条目
   */
  public clearMetrics() {
    performance.clearResourceTimings()
    performance.clearMarks()
    performance.clearMeasures()
  }

  /**
   * 停止监控
   */
  public stopMonitoring() {
    this.isMonitoring = false
  }
}

export default new PerformanceService() 