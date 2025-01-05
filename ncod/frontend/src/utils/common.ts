export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function exponentialBackoff(attempt: number, baseDelay: number): number {
  return baseDelay * Math.pow(2, attempt)
}

export class RetryError extends Error {
  constructor(
    message: string,
    public attempts: number,
    public lastError: any
  ) {
    super(message)
    this.name = 'RetryError'
  }
} 