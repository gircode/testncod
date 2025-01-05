export enum DeviceErrorCodes {
  DEVICE_NOT_FOUND = 'DEVICE_NOT_FOUND',
  DEVICE_BUSY = 'DEVICE_BUSY',
  DEVICE_OFFLINE = 'DEVICE_OFFLINE',
  CONNECTION_FAILED = 'CONNECTION_FAILED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  TIMEOUT = 'TIMEOUT',
  NETWORK_ERROR = 'NETWORK_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

export class DeviceError extends Error {
  code: DeviceErrorCodes
  details?: any

  constructor(message: string, code: DeviceErrorCodes, details?: any) {
    super(message)
    this.name = 'DeviceError'
    this.code = code
    this.details = details
  }
}

export type DeviceErrorCode = typeof DeviceErrorCodes[keyof typeof DeviceErrorCodes] 